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
    "识别图中所有文字块,只输出 JSON 数组(不要任何多余文字、不要 markdown 围栏):\n"
    '[{"text":"该块文字","bbox":[x1,y1,x2,y2]}]\n'
    "bbox = 文字块左上角(x1,y1)与右下角(x2,y2),用图片的实际像素坐标。"
)


def _clamp01(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, number))


def _norm(value: Any, dim: int) -> float:
    """把一个坐标归一化到 0~1。容错三种约定:已是 0~1 直接用;否则按像素 / 0-1000 除以维度。

    (VL 模型实测:Qwen2.5-VL 返绝对像素、Qwen3-VL 返 0-1000、有的听话返 0-1——这里都吃下。)
    """
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 0.0
    if -1.0 <= v <= 1.0:
        return v
    return v / dim if dim else 0.0


def _coords_to_box(item: dict, width: int, height: int):
    """从一条结果里取坐标,统一成归一化 {x,y,w,h};取不到返回 None。

    兼容:bbox/bbox_2d/box_2d = [x1,y1,x2,y2] 角点;box = {x,y,w,h} 或 {x1,y1,x2,y2}。
    """
    corners = item.get("bbox") or item.get("bbox_2d") or item.get("box_2d")
    if isinstance(corners, (list, tuple)) and len(corners) >= 4:
        nx1, ny1 = _norm(corners[0], width), _norm(corners[1], height)
        nx2, ny2 = _norm(corners[2], width), _norm(corners[3], height)
        return {"x": _clamp01(min(nx1, nx2)), "y": _clamp01(min(ny1, ny2)),
                "w": _clamp01(abs(nx2 - nx1)), "h": _clamp01(abs(ny2 - ny1))}
    box = item.get("box")
    if isinstance(box, dict):
        if "w" in box or "h" in box:
            return {"x": _clamp01(_norm(box.get("x"), width)), "y": _clamp01(_norm(box.get("y"), height)),
                    "w": _clamp01(_norm(box.get("w"), width)), "h": _clamp01(_norm(box.get("h"), height))}
        if "x2" in box:
            nx1, ny1 = _norm(box.get("x1"), width), _norm(box.get("y1"), height)
            nx2, ny2 = _norm(box.get("x2"), width), _norm(box.get("y2"), height)
            return {"x": _clamp01(min(nx1, nx2)), "y": _clamp01(min(ny1, ny2)),
                    "w": _clamp01(abs(nx2 - nx1)), "h": _clamp01(abs(ny2 - ny1))}
    return None


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
    def _parse(text: str, width: int, height: int) -> List[dict]:
        import json
        data = json.loads(_strip_fence(text))
        if isinstance(data, dict):
            raw_blocks = data.get("blocks") or data.get("results") or data.get("data") or []
        else:
            raw_blocks = data
        blocks = []
        for item in raw_blocks or []:
            if not isinstance(item, dict):
                continue
            box = _coords_to_box(item, width, height)
            if box is None:
                continue
            blocks.append({"text": str(item.get("text", "") or item.get("label", "")), "box": box})
        return blocks

    async def locate(self, image_path) -> List[dict]:
        from PIL import Image
        with Image.open(image_path) as image:
            width, height = image.size
        client = self._get_client()
        messages = self._build_messages(self._image_data_uri(image_path))
        # 不强制 response_format:VL 模型对它支持不一,靠 prompt + 容错解析(_strip_fence)更稳
        async with _get_sem():
            resp = await client.chat.completions.create(model=self._model, messages=messages)
        return self._parse(resp.choices[0].message.content or "", width, height)


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
