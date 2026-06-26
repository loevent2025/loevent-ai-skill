"""图像文字定位 / OCR 多供应商(P3.6:多模态 VL 模型,§9「定位可靠宿主多模态」)。

GCV(poster_text 内,精确)之外的国产档:用 Qwen-VL / GLM-4V「看图返回文字框」。
精度介于 GCV(精确)和纯人工估位之间——「粗略够用」,用户可在 HTML 编辑器拖准。

配置:LOEVENT_OCR_PROVIDER (qwen-vl / glm-4v / 自定义 base_url) + LOEVENT_OCR_MODEL + LOEVENT_OCR_API_KEY。
没配 → None,poster_text 的 ocr 退到 GCV(再没有就估位)。真机未验证(理论兼容)。
"""
import os
import base64
import logging
from pathlib import Path
from typing import Any, List, Optional

from ..llm_client import _get_sem
from .openai_compat import _strip_fence

logger = logging.getLogger(__name__)

_OCR_PRESETS = {
    "qwen-vl": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "glm-4v": "https://open.bigmodel.cn/api/paas/v4/",
}

_OCR_PROMPT = (
    "识别这张图里所有的文字块。只输出 JSON:"
    '{"blocks":[{"text":"该块文字","box":{"x":0,"y":0,"w":0,"h":0}}]}。'
    "box 为相对图片宽高的归一化值(0~1):x/y 是文字块左上角,w/h 是宽高。不要任何多余文字。"
)


def _clamp01(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, number))


class MultimodalOcrProvider:
    def __init__(self, base_url: str, model: str, api_key: str, name: str):
        self._base_url = base_url
        self._model = model
        self._api_key = api_key
        self.name = name
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError as e:
                raise RuntimeError("缺 openai 依赖:pip install openai。") from e
            self._client = AsyncOpenAI(base_url=self._base_url, api_key=self._api_key)
        return self._client

    @staticmethod
    def _image_data_uri(image_path) -> str:
        raw = Path(image_path).read_bytes()
        return "data:image/png;base64," + base64.b64encode(raw).decode()

    def _build_messages(self, data_uri: str) -> List[dict]:
        return [{"role": "user", "content": [
            {"type": "text", "text": _OCR_PROMPT},
            {"type": "image_url", "image_url": {"url": data_uri}},
        ]}]

    @staticmethod
    def _parse(text: str) -> List[dict]:
        import json
        data = json.loads(_strip_fence(text))
        raw_blocks = data.get("blocks", data) if isinstance(data, dict) else data
        blocks = []
        for item in raw_blocks or []:
            if not isinstance(item, dict):
                continue
            box = item.get("box") or {}
            blocks.append({
                "text": str(item.get("text", "")),
                "box": {"x": _clamp01(box.get("x")), "y": _clamp01(box.get("y")),
                        "w": _clamp01(box.get("w")), "h": _clamp01(box.get("h"))},
            })
        return blocks

    async def locate(self, image_path) -> List[dict]:
        client = self._get_client()
        messages = self._build_messages(self._image_data_uri(image_path))
        async with _get_sem():
            resp = await client.chat.completions.create(
                model=self._model, messages=messages, response_format={"type": "json_object"})
        return self._parse(resp.choices[0].message.content or "")


def resolve_ocr_provider() -> Optional[MultimodalOcrProvider]:
    """读 LOEVENT_OCR_* 决定国产文字定位;没配 / 选 gcv → None(poster_text 退 GCV 或估位)。"""
    name = os.environ.get("LOEVENT_OCR_PROVIDER", "").strip().lower()
    base_url = os.environ.get("LOEVENT_OCR_BASE_URL", "").strip()
    model = os.environ.get("LOEVENT_OCR_MODEL", "").strip()
    api_key = os.environ.get("LOEVENT_OCR_API_KEY", "").strip()

    if not name and not base_url:
        return None
    if name in ("gcv", "google", "vision"):
        return None                       # 显式 GCV → poster_text 走原 GCV 实现

    base = base_url or _OCR_PRESETS.get(name)
    if not base:
        raise RuntimeError(f"未知 OCR 供应商 '{name}'。可选:{', '.join(sorted(_OCR_PRESETS))};"
                           "或用 LOEVENT_OCR_BASE_URL 自定义。")
    if not model:
        raise RuntimeError("OCR 供应商缺 model:请设 LOEVENT_OCR_MODEL(如 qwen-vl-max / glm-4v)。")
    if not api_key:
        raise RuntimeError("OCR 供应商缺 key:请设 LOEVENT_OCR_API_KEY。")

    logger.warning("OCR 走多模态 VL '%s'(理论兼容、真机未验证):文字框为模型估计,精度不及 GCV,"
                   "请在 HTML 编辑器里拖准。", name or base)
    return MultimodalOcrProvider(base, model, api_key, name or base)
