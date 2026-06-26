"""多供应商路由层(P0–P3.5:文本 OpenAI 兼容 + 联网搜索 + 文生图 + 图像编辑/消字)。

get_llm_client() 调 build_client():配了文本 / 图像 / 消字 provider 任一 → 返回 MultiProviderClient;
都没配 → 返回 None,调用方走现状 Gemini 默认路径。

MultiProviderClient 路由:
  - generate           → 文本 provider(配了 OpenAI 兼容,否则回落 Gemini)
  - generate_image     → 纯文本 prompt = 文生图,走文生图 provider;含图 prompt = 编辑/消字,走消字 provider;
                         任一缺位 → Gemini 兜底 → 再没有就报错(消字还可退到 poster_text 本地 erase)

加一家供应商 = presets.py 加一行 + 用户填字段;不改这里的逻辑。
"""
import os
from typing import Any, Optional

from .config import resolve_text_provider, resolve_image_provider, resolve_image_edit_provider
from .openai_compat import OpenAICompatClient
from .image_openai import OpenAICompatImageProvider
from .image_edit import DashScopeImageEditProvider

__all__ = ["build_client", "MultiProviderClient",
           "resolve_text_provider", "resolve_image_provider", "resolve_image_edit_provider"]


def _has_image_object(prompt: Any) -> bool:
    """prompt 是否含图像对象(PIL.Image/bytes 等非 str)——含 = 编辑/消字,纯文本 = 文生图。"""
    items = prompt if isinstance(prompt, (list, tuple)) else [prompt]
    return any(not isinstance(item, str) for item in items)


class MultiProviderClient:
    """对外和 GeminiSingleKeyClient 同接口。四路:文本 / 文生图 / 消字 / Gemini 兜底。"""

    def __init__(self, text_client: Optional[Any], image_t2i: Optional[Any],
                 image_fallback: Optional[Any], image_edit: Optional[Any] = None):
        self._text = text_client
        self._image_t2i = image_t2i
        self._image_edit = image_edit
        self._image_fallback = image_fallback

    async def generate(self, **kwargs):
        if self._text is None:
            raise RuntimeError("只配了图像供应商、且无文本供应商也无 GEMINI_API_KEY:无法生成文本。"
                               "请设 LOEVENT_TEXT_PROVIDER 或 GEMINI_API_KEY。")
        return await self._text.generate(**kwargs)

    async def generate_image(self, **kwargs):
        # 判定靠「prompt 是否含图像对象」而非 isinstance(str)——skill 恒传 list(如 [generation_prompt])。
        if not _has_image_object(kwargs.get("prompt")):
            # 文生图:配置的文生图 provider 优先,否则 Gemini
            if self._image_t2i is not None:
                return await self._image_t2i.generate_image(**kwargs)
            if self._image_fallback is not None:
                return await self._image_fallback.generate_image(**kwargs)
            raise RuntimeError("文生图未配 LOEVENT_IMAGE_PROVIDER 且无 GEMINI_API_KEY。")
        # 编辑/消字(含图):配置的消字 provider 优先,否则 Gemini,再没有让调用方退到本地 erase
        if self._image_edit is not None:
            return await self._image_edit.generate_image(**kwargs)
        if self._image_fallback is not None:
            return await self._image_fallback.generate_image(**kwargs)
        raise RuntimeError(
            "图像编辑/消字未配 LOEVENT_IMAGE_EDIT_PROVIDER 且无 GEMINI_API_KEY;"
            "可用 poster_text 的本地 erase 兜底(不依赖任何图像 API)。"
        )


_cache: dict = {}


def build_client(*, text_model: Optional[str] = None, image_model: Optional[str] = None):
    """文本 / 图像 / 消字 provider 任一配了就返回 MultiProviderClient,否则 None(走 Gemini 默认)。"""
    text_cfg = resolve_text_provider()
    image_cfg = resolve_image_provider()
    edit_cfg = resolve_image_edit_provider()
    if text_cfg is None and image_cfg is None and edit_cfg is None:
        return None

    cache_key = (text_cfg, image_cfg, edit_cfg, image_model)
    client = _cache.get(cache_key)
    if client is not None:
        return client

    has_gemini = bool(os.environ.get("GEMINI_API_KEY", "").strip())

    if text_cfg is not None:
        text_client = OpenAICompatClient(text_cfg)
    elif has_gemini:
        from ..llm_client import GeminiSingleKeyClient   # 懒导入避免循环
        text_client = GeminiSingleKeyClient()
    else:
        text_client = None                               # 只配了图像/消字、又没 Gemini key

    image_t2i = OpenAICompatImageProvider(image_cfg) if image_cfg is not None else None
    image_edit = DashScopeImageEditProvider(edit_cfg) if edit_cfg is not None else None

    image_fallback = None
    if has_gemini:
        from ..llm_client import GeminiSingleKeyClient
        image_fallback = GeminiSingleKeyClient(image_model=image_model)

    client = MultiProviderClient(text_client, image_t2i, image_fallback, image_edit)
    _cache[cache_key] = client
    return client
