"""图像编辑/消字供应商(P3.5:qwen-image-edit via DashScope,指令式)。

对接 poster_text 的消字调用:generate_image(prompt=[ERASE_PROMPT, PIL.Image]) —— 指令式、无 mask,
正好对应 DashScope 多模态生成端点(同步、接受 base64 输入图、返回图片 URL)。
没配本供应商时,MultiProviderClient 会退到 Gemini 或 poster_text 的本地 erase,流程不断。

真机未验证(理论兼容):DashScope 私有格式,逻辑已 no-key 测,换真实 key 再验证消字效果。
"""
import io
import base64
import logging
from typing import Any, Optional, Tuple

from ..llm_client import ImageResponse, _get_sem
from .config import ImageEditConfig

logger = logging.getLogger(__name__)

_TIMEOUT = 60.0


def _split_edit_prompt(prompt: Any) -> Tuple[str, Any]:
    """把 [指令文本…, 图像] 拆成 (instruction, image_obj)。"""
    if not isinstance(prompt, (list, tuple)):
        raise RuntimeError("图像编辑需要 [指令文本, 图像] 形式的 prompt。")
    texts, image = [], None
    for item in prompt:
        if isinstance(item, str):
            texts.append(item)
        elif image is None:
            image = item
    if image is None:
        raise RuntimeError("图像编辑 prompt 里没有图像对象。")
    return "\n".join(texts), image


def _image_to_data_uri(image: Any) -> str:
    """PIL.Image / bytes → data:image/png;base64,... (DashScope 接受的内联图)。"""
    if hasattr(image, "save"):                       # PIL.Image
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        raw = buffer.getvalue()
    elif isinstance(image, (bytes, bytearray)):
        raw = bytes(image)
    else:
        raise RuntimeError(f"不支持的图像类型: {type(image).__name__}(需 PIL.Image 或 bytes)。")
    return "data:image/png;base64," + base64.b64encode(raw).decode()


class DashScopeImageEditProvider:
    def __init__(self, cfg: ImageEditConfig):
        self._cfg = cfg

    def _build_body(self, instruction: str, data_uri: str) -> dict:
        return {
            "model": self._cfg.model,
            "input": {"messages": [{"role": "user", "content": [
                {"image": data_uri},
                {"text": instruction},
            ]}]},
        }

    @staticmethod
    def _extract_image_url(data: dict) -> Optional[str]:
        try:
            content = data["output"]["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return None
        for part in content or []:
            if isinstance(part, dict) and part.get("image"):
                return part["image"]
        return None

    async def generate_image(self, *, module: str, prompt: Any, aspect_ratio: str = "1:1",
                             image_size: str = "1K") -> ImageResponse:
        instruction, image = _split_edit_prompt(prompt)
        body = self._build_body(instruction, _image_to_data_uri(image))
        import httpx
        async with _get_sem():
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.post(
                    self._cfg.base_url,
                    headers={"Authorization": f"Bearer {self._cfg.api_key}", "Content-Type": "application/json"},
                    json=body,
                )
                resp.raise_for_status()
                url = self._extract_image_url(resp.json())
                if not url:
                    raise RuntimeError(f"图像编辑供应商 '{self._cfg.name}' 未返回图片(module={module})。")
                fetched = await client.get(url)
                fetched.raise_for_status()
                return ImageResponse(image_bytes=fetched.content, mime_type="image/png", raw=None)
