"""OpenAI 兼容的文本供应商(GLM/DeepSeek/Qwen/Kimi/… 直连或经网关)。

与 GeminiSingleKeyClient 同接口(generate / generate_image),业务零改动即可换底座。
只做文本 + 结构化输出;联网搜索走外部搜索(P2);图像由 MultiProviderClient 路由到图像供应商。

grounding 默认**严格**:要 grounding 却拿不到外部搜索结果时直接报错(不静默编造),
确需无来源结果时设 LOEVENT_ALLOW_UNGROUNDED=1 显式放行。
"""
import os
import json
import asyncio
import logging
from typing import Any, Dict, List, Optional

from ..llm_client import LLMResponse, _is_transient, _get_sem
from .config import TextProviderConfig

logger = logging.getLogger(__name__)

# OpenAI 的 finish_reason → 对齐 Gemini/runtime 的命名(runtime 用 'MAX_TOKENS' 判截断)
_FINISH_REASON_MAP = {"length": "MAX_TOKENS", "stop": "STOP",
                      "content_filter": "CONTENT_FILTER", "tool_calls": "TOOL_CALLS"}


def _strip_fence(text: str) -> str:
    """剥 ```json ... ``` 围栏,仅用于校验判断;返回给业务的仍是原文(下游 parse_structured 自己剥)。"""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1] if "\n" in t else t[3:]
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()


def _prompt_to_text(prompt: Any) -> str:
    """把 prompt 归一成单条文本。

    list[str] 用空行拼接(skill 常传 [text] / [text1, text2]);含 PIL.Image/bytes 等多模态对象
    → 显式报错(OpenAI 兼容文本端不吃多模态)。绝不用 json.dumps 把 list 序列化成字面量、或抛裸 TypeError。
    """
    if isinstance(prompt, str):
        return prompt
    if isinstance(prompt, (list, tuple)):
        parts = []
        for item in prompt:
            if isinstance(item, str):
                parts.append(item)
            else:
                raise RuntimeError(
                    f"当前文本供应商不支持多模态输入(prompt 含 {type(item).__name__});"
                    "参考图分析/图像编辑这类多模态调用请用 Gemini,或等多模态多供应商支持。")
        return "\n\n".join(parts)
    return str(prompt)


def _native_search_extra_body(native_search: str):
    """该供应商的「原生联网搜索」怎么并进 chat 请求(走 openai SDK 的 extra_body,直达请求体)。

    返回 None = 没有可自动用的原生搜索(Kimi 的 $web_search 是多步、豆包要控制台开插件、DeepSeek 无)
    → 调用方回落到外部搜索。理论兼容、真机未验证,换真实 key 再核实各家参数。
    """
    if native_search == "enable_search":      # 通义 Qwen / DashScope
        return {"enable_search": True}
    if native_search == "web_search_tool":    # 智谱 GLM
        return {"tools": [{"type": "web_search", "web_search": {"enable": True, "search_engine": "search_pro"}}]}
    if native_search == "web_search_top":     # 百度文心 ERNIE
        return {"web_search": {"enable": True}}
    return None


class OpenAICompatClient:
    def __init__(self, cfg: TextProviderConfig):
        self._cfg = cfg
        self._client = None   # 懒建,避免无 key 时构造 / 绑错事件循环

    def _get_client(self):
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError as e:
                raise RuntimeError("缺 openai 依赖:pip install openai(或 pip install -r requirements.txt)。") from e
            self._client = AsyncOpenAI(base_url=self._cfg.base_url, api_key=self._cfg.api_key)
        return self._client

    async def generate(self, *, module: str, prompt: Any, system_prompt: Optional[str] = None,
                       response_schema: Optional[Any] = None, use_google_search: bool = False,
                       enable_url_context: bool = False, enable_thinking: bool = False,
                       max_output_tokens: Optional[int] = None,
                       history: Optional[List[Dict[str, Any]]] = None) -> LLMResponse:
        grounding_source = None
        native_search_body = None
        if use_google_search or enable_url_context:
            # 混合:有原生搜索的家(且没显式配外部)→ 走原生(一次调用,模型自己搜+答);
            #       没原生 / 显式配了外部 → 走外部两步(Bocha/Tavily)。
            search_env = os.environ.get("LOEVENT_SEARCH_PROVIDER", "").strip().lower()
            explicit_external = search_env not in ("", "none")
            native_search_body = None if explicit_external else _native_search_extra_body(self._cfg.native_search)
            if native_search_body is not None:
                grounding_source = f"{self._cfg.name}_native"
            else:
                prompt, grounding_source = await self._apply_grounding(prompt, module)

        messages = self._build_messages(system_prompt, prompt, response_schema, history)
        request = self._build_request(messages, response_schema, max_output_tokens)
        if native_search_body is not None:
            request.setdefault("extra_body", {}).update(native_search_body)
        resp = await self._call(request, module)
        text = self._content_of(resp)

        validate = response_schema is not None and hasattr(response_schema, "model_validate_json")
        if validate and not self._is_valid(text, response_schema):
            # 一次重试:把"上次输出不合法"喂回去(B 档 json_object 常见)
            retry = dict(request)
            retry["messages"] = messages + [
                {"role": "assistant", "content": text},
                {"role": "user", "content": "上次输出不是合法的目标 JSON。请**只**输出符合 schema 的 JSON,不要任何多余文字或 markdown 围栏。"},
            ]
            resp = await self._call(retry, module)
            text = self._content_of(resp)

        return LLMResponse(
            text=text,
            used_google_search=bool(grounding_source and grounding_source != "none"),
            grounding_source=grounding_source,
            finish_reason=self._finish_reason_of(resp),
            output_tokens=self._output_tokens_of(resp),
        )

    # ── grounding 两步编排(P2:外部搜索作基座;默认严格不编造)──────────
    async def _apply_grounding(self, prompt, module):
        """提议查询→外部搜索→把结果拼进 prompt。返回 (新 prompt, grounding_source)。

        默认严格:拿不到外部结果就报错(让 skill 走降级分支,而非静默编造)。
        设 LOEVENT_ALLOW_UNGROUNDED=1 → 放行,原样 prompt + 'none' + 告警。
        """
        from .grounding import resolve_grounding_provider
        allow = os.environ.get("LOEVENT_ALLOW_UNGROUNDED", "").strip().lower() not in ("", "0", "false", "no")
        grounding = resolve_grounding_provider()
        if grounding is None:
            if allow:
                logger.warning("module=%s:未配 LOEVENT_SEARCH_PROVIDER 且已开 LOEVENT_ALLOW_UNGROUNDED → "
                               "本次无实时 grounding,结果可能过时/编造,请人工核实。", module)
                return prompt, "none"
            raise RuntimeError(
                "联网调研需要搜索能力,但未配 LOEVENT_SEARCH_PROVIDER —— trends/guests/event-strategy 这类 skill "
                "不应无来源编造。请配 LOEVENT_SEARCH_PROVIDER=bocha|tavily + LOEVENT_SEARCH_API_KEY;"
                "若确实接受无实时来源,设 LOEVENT_ALLOW_UNGROUNDED=1。")
        queries = await self._propose_queries(prompt, module)
        results = []
        for query in queries[:3]:
            try:
                async with _get_sem():   # 外部搜索也纳入并发限流(company 等会并行打很多 grounding)
                    found = await grounding.search(query)
                results.extend(found)
            except Exception as e:
                logger.warning("module=%s 搜索 '%s' 失败: %s: %s", module, query, type(e).__name__, e)
        if not results:
            if allow:
                logger.warning("module=%s:已配外部搜索 '%s' 但本次未取到结果,已开 LOEVENT_ALLOW_UNGROUNDED → "
                               "降级为无 grounding,请人工核实。", module, grounding.name)
                return prompt, "none"
            raise RuntimeError(
                f"已配外部搜索 '{grounding.name}' 但本次未取到任何结果;为避免无来源编造已中止。"
                "请检查搜索 key/配额/网络,或设 LOEVENT_ALLOW_UNGROUNDED=1 接受无 grounding。")
        return self._inject_results(prompt, results), grounding.name

    async def _propose_queries(self, prompt, module) -> List[str]:
        ask = [
            {"role": "system", "content": "你是检索助手。只输出 JSON:{\"queries\": [\"...\"]},给完成下面任务最该跑的 1-3 条简洁中文/英文网络搜索查询,不要任何多余文字。"},
            {"role": "user", "content": _prompt_to_text(prompt)},
        ]
        try:
            resp = await self._call({"model": self._cfg.model, "messages": ask,
                                     "response_format": {"type": "json_object"}}, module)
            queries = json.loads(_strip_fence(self._content_of(resp))).get("queries", [])
            cleaned = [q for q in queries if isinstance(q, str) and q.strip()]
            if cleaned:
                return cleaned
        except Exception as e:
            logger.warning("module=%s 提议查询失败,回退用原 prompt 当查询: %s", module, e)
        return [_prompt_to_text(prompt)[:200]]

    @staticmethod
    def _inject_results(prompt, results) -> str:
        lines = [f"- [{r.title}]({r.url}) {r.snippet} {('(' + r.published_at + ')') if r.published_at else ''}".strip()
                 for r in results[:10]]
        block = "\n".join(lines)
        return ("以下是实时联网搜索到的资料(请**基于这些**作答,涉及事实处标注来源 URL,不要编造):\n"
                f"{block}\n\n---\n任务:\n{_prompt_to_text(prompt)}")

    async def generate_image(self, *, module: str, prompt: Any, aspect_ratio: str = "1:1", image_size: str = "1K"):
        # 正常不会走到这里:图像由 MultiProviderClient 路由到图像供应商或 Gemini 兜底
        raise RuntimeError(f"文本供应商 '{self._cfg.name}' 不出图;图像应经 MultiProviderClient 的图像路由。")

    # ── 纯逻辑(无 key 可单测)─────────────────────────────
    def _build_messages(self, system_prompt, prompt, response_schema, history) -> List[Dict[str, Any]]:
        messages: List[Dict[str, Any]] = []
        system_text = system_prompt or ""
        # B 档:把 schema 描述塞进 system(并自然带上 "json" 关键词,满足 needs_json_keyword 的家)
        if response_schema is not None and self._cfg.structured_tier != "json_schema":
            system_text = (system_text + "\n\n" + self._schema_hint(response_schema)).strip()
        if system_text:
            messages.append({"role": "system", "content": system_text})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": _prompt_to_text(prompt)})
        return messages

    def _schema_hint(self, response_schema) -> str:
        schema = response_schema.model_json_schema() if hasattr(response_schema, "model_json_schema") else response_schema
        return ("Respond ONLY with valid JSON matching this schema (no markdown, no prose):\n"
                + json.dumps(schema, ensure_ascii=False))

    def _build_request(self, messages, response_schema, max_output_tokens) -> Dict[str, Any]:
        request: Dict[str, Any] = {"model": self._cfg.model, "messages": messages}
        if max_output_tokens is not None:
            request["max_tokens"] = max_output_tokens
        if response_schema is not None:
            if self._cfg.structured_tier == "json_schema" and hasattr(response_schema, "model_json_schema"):
                request["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {"name": response_schema.__name__, "schema": response_schema.model_json_schema()},
                }
            else:
                request["response_format"] = {"type": "json_object"}
        return request

    @staticmethod
    def _is_valid(text: str, response_schema) -> bool:
        try:
            response_schema.model_validate_json(_strip_fence(text))
            return True
        except Exception:
            return False

    @staticmethod
    def _content_of(resp: Any) -> str:
        try:
            return resp.choices[0].message.content or ""
        except Exception:
            return ""

    @staticmethod
    def _finish_reason_of(resp: Any) -> Optional[str]:
        try:
            fr = resp.choices[0].finish_reason
        except Exception:
            return None
        if not fr:
            return None
        return _FINISH_REASON_MAP.get(fr, fr.upper() if isinstance(fr, str) else fr)

    @staticmethod
    def _output_tokens_of(resp: Any) -> Optional[int]:
        usage = getattr(resp, "usage", None)
        return getattr(usage, "completion_tokens", None) if usage else None

    # ── 网络调用(限流 + 瞬时错误重试),返回原始 resp 供上层取 content/finish_reason/usage ──
    async def _call(self, request: Dict[str, Any], module: str) -> Any:
        client = self._get_client()
        resp = None
        async with _get_sem():
            for attempt in range(3):
                try:
                    resp = await client.chat.completions.create(**request)
                    break
                except Exception as e:
                    if attempt < 2 and _is_transient(e):
                        await asyncio.sleep(1.5 * (attempt + 1))
                        continue
                    logger.warning("module=%s provider=%s 调用失败: %s: %s",
                                   module, self._cfg.name, type(e).__name__, e)
                    raise
        return resp
