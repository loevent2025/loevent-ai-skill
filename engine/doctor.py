"""
环境自检(给用户的 agent 跑):验 Key、探模型可达、报告降级项。

用法: python -m engine.doctor   (或 python engine/doctor.py)
"""

import asyncio
import os
import sys

# 允许 `python engine/doctor.py` 直接跑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import get_llm_client  # noqa: E402
from engine.model_config import (  # noqa: E402
    MODEL_GEMINI_TEXT,
    MODEL_GEMINI_TEXT_FALLBACK,
    MODEL_GEMINI_IMAGE,
)


async def _probe_text(model_label: str) -> bool:
    try:
        llm = get_llm_client()
        resp = await llm.generate(module="doctor", prompt="ping，请只回复一个字: ok")
        return bool((resp.text or "").strip())
    except Exception as e:
        print(f"   ✗ {model_label} 不可达: {type(e).__name__}: {e}")
        return False


async def main() -> int:
    print("== LoEvent AI Skill · 环境自检 ==")
    ok = True

    # 1) Key
    if not os.environ.get("GEMINI_API_KEY", "").strip():
        print("✗ 未检测到 GEMINI_API_KEY。请在 .env 设置或 export。")
        return 1
    print("✓ GEMINI_API_KEY 已设置")

    # 2) 文本模型可达(grounding 也走这个)
    print(f"· 探测文本模型 {MODEL_GEMINI_TEXT} …")
    if await _probe_text(MODEL_GEMINI_TEXT):
        print(f"✓ 文本管线可用(默认 {MODEL_GEMINI_TEXT},fallback {MODEL_GEMINI_TEXT_FALLBACK})")
    else:
        print("✗ 文本模型不可达 —— 所有文本类 skill 无法运行,请检查 Key/配额。")
        ok = False

    # 3) 图像档(海报类需要;免费 Key 大概率不行 → 降级)
    print(f"· 探测图像档权限 {MODEL_GEMINI_IMAGE} …")
    try:
        llm = get_llm_client()
        await llm.generate_image(module="doctor", prompt="a tiny gray dot on white", image_size="1K")
        print("✓ 图像档可用(skill-poster 可生图)")
    except Exception as e:
        print(f"⚠ 图像档不可用 → skill-poster 降级/跳过生图(文本类 skill 不受影响)。原因: {type(e).__name__}")

    # 4) OCR / Maps(单 Key 搞不定,仅提示)
    print("⚠ 海报精修 OCR(Google Cloud Vision)与地图 Key(Maps)需另配服务账号,"
          "未配则 poster 精修/地理编码自动跳过。")

    print("== 自检完成 ==")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
