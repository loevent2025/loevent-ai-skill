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
    MODEL_GEMINI_GROUNDING,
    MODEL_GEMINI_IMAGE,
)


async def _probe_text(model_label: str, *, use_google_search: bool = False) -> bool:
    try:
        llm = get_llm_client()
        resp = await llm.generate(
            module="doctor", prompt="ping，请只回复一个字: ok",
            use_google_search=use_google_search,
        )
        return bool((resp.text or "").strip())
    except Exception as e:
        print(f"   ✗ {model_label} 不可达: {type(e).__name__}: {e}")
        return False


async def main() -> int:
    print("== LoEvent AI Skill · 环境自检 ==")
    ok = True

    # 先判活动路径:配了多供应商(LOEVENT_TEXT_*)就探它,否则回落 Gemini(GEMINI_API_KEY)
    from engine.providers.config import resolve_text_provider, resolve_image_provider
    from engine.providers.grounding import resolve_grounding_provider
    try:
        text_cfg = resolve_text_provider()
    except Exception as e:
        print(f"✗ 文本供应商配置有误(LOEVENT_TEXT_*): {e}")
        return 1
    has_gemini = bool(os.environ.get("GEMINI_API_KEY", "").strip())

    # 1) 文本路径
    if text_cfg is not None:
        tag = "官方实测背书" if text_cfg.supported else "理论兼容,自行验证"
        print(f"· 文本走多供应商: {text_cfg.name}({text_cfg.base_url};{tag})…")
        if await _probe_text(text_cfg.name):
            print(f"✓ 文本管线可用(provider={text_cfg.name},结构化档 {text_cfg.structured_tier})")
        else:
            print("✗ 文本供应商不可达 —— 检查 LOEVENT_TEXT_BASE_URL/MODEL/API_KEY 与网络。")
            ok = False
    elif has_gemini:
        print(f"· 文本走 Gemini {MODEL_GEMINI_TEXT} …")
        if await _probe_text(MODEL_GEMINI_TEXT):
            print(f"✓ 文本管线可用(Gemini {MODEL_GEMINI_TEXT},fallback {MODEL_GEMINI_TEXT_FALLBACK})")
        else:
            print("✗ 文本模型不可达 —— 检查 GEMINI_API_KEY/配额。")
            ok = False
    else:
        print("✗ 既未配 LOEVENT_TEXT_PROVIDER,也没有 GEMINI_API_KEY —— 无法运行任何文本 skill。")
        print("   国内示例: export LOEVENT_TEXT_PROVIDER=glm LOEVENT_TEXT_MODEL=… LOEVENT_TEXT_API_KEY=…")
        return 1

    # 2) grounding(联网调研:trends/company/guests/budget)
    try:
        search = resolve_grounding_provider()
    except Exception as e:
        search = None
        print(f"⚠ 搜索供应商配置有误(LOEVENT_SEARCH_*): {e}")
    if text_cfg is not None:
        if search is not None:
            print(f"✓ 外部搜索已配({search.name})→ 联网调研走外部(显式覆盖原生)")
        elif text_cfg.native_search:
            print(f"✓ {text_cfg.name} 有原生联网搜索 → 联网调研默认走它的原生(没配外部也行)")
        else:
            print(f"⚠ {text_cfg.name} 无原生搜索、也未配 LOEVENT_SEARCH_PROVIDER → 联网调研类 skill 默认**报错中止**"
                  "(避免无来源编造);请配 bocha/tavily(+LOEVENT_SEARCH_API_KEY),或设 LOEVENT_ALLOW_UNGROUNDED=1。")
    elif has_gemini:
        print(f"· 探测 Gemini grounding {MODEL_GEMINI_GROUNDING} …")
        if await _probe_text(MODEL_GEMINI_GROUNDING, use_google_search=True):
            print(f"✓ Gemini grounding 可用(trends/company/guests/budget 走 {MODEL_GEMINI_GROUNDING})")
        else:
            print("⚠ Gemini grounding 不可达 → 联网调研类 skill 可能降级/失败;纯文本类不受影响。")

    # 3) 图像档(海报生图)
    try:
        image_cfg = resolve_image_provider()
    except Exception as e:
        image_cfg = None
        print(f"⚠ 图像供应商配置有误(LOEVENT_IMAGE_*): {e}")
    if image_cfg is not None:
        tag = "官方实测背书" if image_cfg.supported else "理论兼容,自行验证"
        print(f"✓ 文生图走多供应商: {image_cfg.name}({tag})——真实可用性请跑一次海报验证;"
              "编辑/消字仍需 Gemini 或 poster_text 本地 erase。")
    elif has_gemini:
        print(f"· 探测 Gemini 图像档 {MODEL_GEMINI_IMAGE} …")
        try:
            llm = get_llm_client()
            await llm.generate_image(module="doctor", prompt="a tiny gray dot on white", image_size="1K")
            print("✓ 图像档可用(skill-poster 可生图)")
        except Exception as e:
            print(f"⚠ 图像档不可用 → skill-poster 降级/跳过生图(文本类 skill 不受影响)。原因: {type(e).__name__}")
    else:
        print("⚠ 既未配 LOEVENT_IMAGE_PROVIDER 也无 GEMINI_API_KEY → 海报生图不可用(文本类 skill 不受影响)。")

    # 5) 海报「文字可编辑」(GCV OCR,service account)—— 可选能力,仅提示
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip():
        print("✓ GOOGLE_APPLICATION_CREDENTIALS 已设置(海报「文字可编辑」的 GCV OCR 可用)")
    else:
        print("⚠ 未设 GOOGLE_APPLICATION_CREDENTIALS(指向 GCV 服务账号 JSON,独立于 GEMINI_API_KEY)→ "
              "海报「文字可编辑」跳过;普通出图与文本类 skill 不受影响。")

    print("== 自检完成 ==")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
