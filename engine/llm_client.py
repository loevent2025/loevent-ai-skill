"""
单 Key 的 Gemini 客户端(单机版:单 GEMINI_API_KEY 直连)

与后端的差别(只在 infra,不在 AI 逻辑):
- 多项目 Key 池 → 单个 genai.Client(api_key=$GEMINI_API_KEY);
- 删掉 resolve_project_for_user 的按用户路由;
- token/错误日志从写 MongoDB → 可选回调 on_tokens(默认 no-op);
- 其余(GenerateContentConfig 构建、response 包装、model fallback、grounding、
  thinking、history/chat、response_schema)与后端 gemini_client.py 逐字对齐。

业务(skill 脚本)只用:
    from engine import get_llm_client
    llm = get_llm_client()
    resp = await llm.generate(module="info_audience", prompt=..., system_prompt=...,
                              response_schema=..., use_google_search=...)
    text = resp.text
"""

import os
import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from google import genai
from google.genai import types
from google.genai.types import GoogleSearch, Tool, UrlContext

from .model_config import (
    MODEL_GEMINI_TEXT,
    MODEL_GEMINI_GROUNDING,
    MODEL_GEMINI_IMAGE,
    get_fallback_model,
)

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """统一文本响应(对齐后端 base.py 的 LLMResponse 字段)。"""
    text: str
    used_google_search: bool = False
    thinking_text: Optional[str] = None
    finish_reason: Optional[str] = None
    output_tokens: Optional[int] = None
    raw: Any = None
    grounding_source: Optional[str] = None   # 多供应商可观测:本次 grounding 来源(gemini_native/bocha/tavily/none)


@dataclass
class ImageResponse:
    image_bytes: bytes
    mime_type: str = "image/png"
    raw: Any = None


# ─────────────────────────────────────────────────────────────
# 单 Key client(进程级单例)
# ─────────────────────────────────────────────────────────────
_genai_client: Optional[genai.Client] = None


def _get_genai_client() -> genai.Client:
    global _genai_client
    if _genai_client is None:
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "缺少 GEMINI_API_KEY。请在 .env 里设置(在 "
                "https://aistudio.google.com/apikey 申请),或 export GEMINI_API_KEY=AIza..."
            )
        _genai_client = genai.Client(api_key=api_key)
    return _genai_client


# 可选 token 回调(替代后端写 token_logs);默认什么都不做
OnTokens = Callable[[Dict[str, Any]], None]
_on_tokens: Optional[OnTokens] = None


def set_token_callback(cb: Optional[OnTokens]) -> None:
    """可选:注册一个 token 用量回调(默认无)。"""
    global _on_tokens
    _on_tokens = cb


# 并发上限(对齐后端 nano_semaphore):像 skill-company 那种一次并发打 ~22 个
# grounding 请求,不限流会打爆连接池 / 触发 SSL EOF。默认 5,可用环境变量覆盖。
# 懒创建:避免在无事件循环时构造 Semaphore 绑错 loop。
_sem: Optional[asyncio.Semaphore] = None


def _get_sem() -> asyncio.Semaphore:
    global _sem
    if _sem is None:
        # 解析容错:非法/负数/0 会让 Semaphore 直接崩或死锁;统一夹到 >=1,默认 5。
        try:
            n = int(os.environ.get("LOEVENT_MAX_CONCURRENCY", "5"))
        except ValueError:
            n = 5
        _sem = asyncio.Semaphore(max(1, n))
    return _sem


def _is_transient(e: Exception) -> bool:
    """瞬时连接类错误(SSL EOF / 连接重置 / 超时)→ 同模型重试,而非切 fallback。"""
    s = f"{type(e).__name__}: {e}".lower()
    return any(k in s for k in (
        "connecterror", "connecttimeout", "readtimeout", "remoteprotocol",
        "ssl", "eof", "connection reset", "connection aborted", "temporarily",
    ))


class GeminiSingleKeyClient:
    """单 Key 版 LLMClient。接口对齐后端 GeminiClient。"""

    def __init__(self, default_model: Optional[str] = None, image_model: Optional[str] = None):
        self._model = default_model or MODEL_GEMINI_TEXT
        self._image_model = image_model or MODEL_GEMINI_IMAGE

    async def generate(
        self,
        *,
        module: str,
        prompt: Any,
        system_prompt: Optional[str] = None,
        response_schema: Optional[Dict[str, Any]] = None,
        use_google_search: bool = False,
        enable_url_context: bool = False,
        enable_thinking: bool = False,
        max_output_tokens: Optional[int] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        config = self._build_text_config(
            system_prompt=system_prompt,
            response_schema=response_schema,
            use_google_search=use_google_search,
            enable_url_context=enable_url_context,
            enable_thinking=enable_thinking,
            max_output_tokens=max_output_tokens,
        )
        # 带 Google Search grounding 的调用固定走专用模型;纯文本/url_context 走默认
        model = MODEL_GEMINI_GROUNDING if use_google_search else self._model
        raw = await self._call_with_fallback(
            model=model, prompt=prompt, config=config,
            history=history, module=module,
        )
        return self._wrap_text_response(raw, module=module, thinking_requested=enable_thinking)

    async def generate_image(
        self,
        *,
        module: str,
        prompt: Any,
        aspect_ratio: str = "1:1",
        image_size: str = "1K",
    ) -> ImageResponse:
        config = types.GenerateContentConfig(
            response_modalities=["Image"],
            image_config=types.ImageConfig(aspect_ratio=aspect_ratio, image_size=image_size),
        )
        raw = await self._call_with_fallback(
            model=self._image_model, prompt=prompt, config=config,
            history=None, module=module,
        )
        return self._wrap_image_response(raw, module=module)

    # ── 调用 + fallback(无 project,单 Key;失败切 fallback 模型重试一次)──
    async def _call_with_fallback(self, *, model, prompt, config, history, module) -> Any:
        try:
            return await self._raw_call(model, prompt, config, history)
        except Exception as e:
            logger.warning("⚠️  module=%s model=%s 调用失败: %s: %s", module, model, type(e).__name__, e)
            fb = get_fallback_model(model)
            if not fb:
                raise
            await asyncio.sleep(2)
            logger.info("↪︎  fallback → %s", fb)
            return await self._raw_call(fb, prompt, config, history)

    async def _raw_call(self, model, prompt, config, history) -> Any:
        client = _get_genai_client()

        def _do():
            if history is not None:
                chat = client.chats.create(model=model, history=history)
                return chat.send_message(prompt, config=config)
            return client.models.generate_content(model=model, contents=prompt, config=config)

        # 限流 + 瞬时连接错误重试(同模型,最多 3 次退避);非瞬时错误直接抛给上层做 model fallback
        async with _get_sem():
            for attempt in range(3):
                try:
                    resp = await asyncio.to_thread(_do)
                    break
                except Exception as e:
                    if attempt < 2 and _is_transient(e):
                        await asyncio.sleep(1.5 * (attempt + 1))
                        continue
                    raise

        # 可选 token 回调(替代后端写 token_logs)
        if _on_tokens is not None:
            try:
                usage = getattr(resp, "usage_metadata", None)
                _on_tokens({
                    "model": model,
                    "tokenInput": getattr(usage, "prompt_token_count", None),
                    "tokenOutput": getattr(usage, "candidates_token_count", None),
                })
            except Exception:
                pass
        return resp

    # ── config 构建(逐字对齐后端 _build_text_config)──
    @staticmethod
    def _build_text_config(*, system_prompt, response_schema, use_google_search,
                           enable_url_context, enable_thinking, max_output_tokens) -> types.GenerateContentConfig:
        kwargs: Dict[str, Any] = {}
        if system_prompt is not None:
            kwargs["system_instruction"] = system_prompt
        if response_schema is not None:
            kwargs["response_mime_type"] = "application/json"
            kwargs["response_schema"] = response_schema
        tools: List[Tool] = []
        if use_google_search:
            tools.append(Tool(google_search=GoogleSearch()))
        if enable_url_context:
            tools.append(Tool(url_context=UrlContext()))
        if tools:
            kwargs["tools"] = tools
        if enable_thinking:
            kwargs["thinking_config"] = types.ThinkingConfig(include_thoughts=True)
        if max_output_tokens is not None:
            kwargs["max_output_tokens"] = max_output_tokens
        return types.GenerateContentConfig(**kwargs)

    # ── response 包装(对齐后端 _wrap_text_response)──
    @staticmethod
    def _wrap_text_response(raw: Any, *, module: str, thinking_requested: bool) -> LLMResponse:
        used_google_search = False
        thinking_text: Optional[str] = None
        answer_text: Optional[str] = None
        finish_reason: Optional[str] = None

        candidates = getattr(raw, "candidates", None)
        if candidates:
            candidate = candidates[0]
            if getattr(candidate, "grounding_metadata", None):
                used_google_search = True
            fr = getattr(candidate, "finish_reason", None)
            if fr is not None:
                finish_reason = getattr(fr, "name", None) or str(fr)
            if thinking_requested:
                thoughts, answers = [], []
                content = getattr(candidate, "content", None)
                parts = getattr(content, "parts", None) if content else None
                for part in parts or []:
                    text = getattr(part, "text", None)
                    if not text:
                        continue
                    (thoughts if getattr(part, "thought", False) else answers).append(text)
                if thoughts:
                    thinking_text = "\n".join(thoughts)
                if answers:
                    answer_text = "\n".join(answers)

        if answer_text is None:
            answer_text = getattr(raw, "text", str(raw))

        output_tokens = None
        usage = getattr(raw, "usage_metadata", None)
        if usage is not None:
            output_tokens = getattr(usage, "candidates_token_count", None)

        return LLMResponse(
            text=answer_text,
            used_google_search=used_google_search,
            thinking_text=thinking_text,
            finish_reason=finish_reason,
            output_tokens=output_tokens,
            raw=raw,
            grounding_source="gemini_native" if used_google_search else None,
        )

    @staticmethod
    def _wrap_image_response(raw: Any, *, module: str) -> ImageResponse:
        candidates = getattr(raw, "candidates", None)
        if not candidates:
            raise ValueError(f"Image generation returned no candidates (module={module})")
        content = getattr(candidates[0], "content", None)
        parts = getattr(content, "parts", None) if content else None
        for part in parts or []:
            inline_data = getattr(part, "inline_data", None)
            if inline_data is not None:
                return ImageResponse(
                    image_bytes=inline_data.data,
                    mime_type=getattr(inline_data, "mime_type", "image/png"),
                    raw=raw,
                )
        raise ValueError(f"Image generation returned no inline_data (module={module})")


# ── 单例工厂(对齐后端 get_llm_client)──
_default_client: Optional[GeminiSingleKeyClient] = None
_custom_clients: Dict[tuple, GeminiSingleKeyClient] = {}


def get_llm_client(*, text_model: Optional[str] = None, image_model: Optional[str] = None):
    # 配了多供应商(LOEVENT_TEXT_PROVIDER/BASE_URL)就走 OpenAI 兼容路由;没配则原样走下面的 Gemini 默认。
    from .providers import build_client   # 懒导入避免与 providers 的循环引用
    routed = build_client(text_model=text_model, image_model=image_model)
    if routed is not None:
        return routed

    global _default_client
    if text_model is None and image_model is None:
        if _default_client is None:
            _default_client = GeminiSingleKeyClient()
        return _default_client
    key = (text_model, image_model)
    client = _custom_clients.get(key)
    if client is None:
        client = GeminiSingleKeyClient(default_model=text_model, image_model=image_model)
        _custom_clients[key] = client
    return client
