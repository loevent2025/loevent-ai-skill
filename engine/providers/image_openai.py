"""OpenAI 兼容的文生图供应商(P3:豆包 Seedream / CogView / OpenAI gpt-image)。

与 GeminiSingleKeyClient.generate_image 同接口,返回 ImageResponse(image_bytes)。
这些家都走 OpenAI 兼容的 images.generate,返回图片 URL(豆包也支持 b64),
本类统一取回 bytes。只做文生图;图像编辑/消字(inpaint)与异步轮询家(万相/可图)留作 P3.5。

尺寸:默认让供应商用自己的默认尺寸(各家允许的 size 列表不一,硬塞易报错);
要控制海报比例,设 LOEVENT_IMAGE_SIZE(如 1024x1536 / 2K,按你的供应商接受的格式)。
"""
import os
import base64
import logging
from typing import Any, Optional

from ..llm_client import ImageResponse, _get_sem
from .config import ImageProviderConfig
from .openai_compat import _prompt_to_text

logger = logging.getLogger(__name__)


class OpenAICompatImageProvider:
    def __init__(self, cfg: ImageProviderConfig):
        self._cfg = cfg
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError as e:
                raise RuntimeError("缺 openai 依赖:pip install openai。") from e
            self._client = AsyncOpenAI(base_url=self._cfg.base_url, api_key=self._cfg.api_key)
        return self._client

    @staticmethod
    def _resolve_size(image_size: str, aspect_ratio: str) -> Optional[str]:
        # 各家允许的 size 格式/列表不一,默认不塞(用供应商默认);要控制比例靠 env 覆盖
        return os.environ.get("LOEVENT_IMAGE_SIZE", "").strip() or None

    async def generate_image(self, *, module: str, prompt: Any, aspect_ratio: str = "1:1",
                             image_size: str = "1K") -> ImageResponse:
        client = self._get_client()
        kwargs = {"model": self._cfg.model, "n": 1, "prompt": _prompt_to_text(prompt)}
        size = self._resolve_size(image_size, aspect_ratio)
        if size:
            kwargs["size"] = size
        async with _get_sem():
            resp = await client.images.generate(**kwargs)
        return await self._to_image_response(resp, module)

    async def _to_image_response(self, resp: Any, module: str) -> ImageResponse:
        data = getattr(resp, "data", None)
        if not data:
            raise RuntimeError(f"文生图供应商 '{self._cfg.name}' 返回空 data(module={module})。")
        return ImageResponse(image_bytes=await self._extract_bytes(data[0]),
                             mime_type="image/png", raw=resp)

    @staticmethod
    async def _extract_bytes(item: Any) -> bytes:
        b64 = getattr(item, "b64_json", None)
        if b64:
            return base64.b64decode(b64)
        url = getattr(item, "url", None)
        if url:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                return resp.content
        raise RuntimeError("文生图供应商返回既无 b64_json 也无 url,无法取回图片。")
