"""model_config 的确定性常量与 fallback 映射(#6 改动的回归网)。"""

from engine.model_config import (
    MODEL_GEMINI_TEXT,
    MODEL_GEMINI_TEXT_FALLBACK,
    MODEL_GEMINI_GROUNDING,
    MODEL_GEMINI_IMAGE,
    MODEL_GEMINI_IMAGE_FALLBACK,
    get_fallback_model,
)


def test_grounding_model_is_dedicated():
    assert MODEL_GEMINI_GROUNDING == "gemini-3.5-flash"


def test_fallback_chain():
    assert get_fallback_model(MODEL_GEMINI_TEXT) == MODEL_GEMINI_TEXT_FALLBACK
    # grounding 模型失败 → 回落默认文本模型(它同样支持 Google Search)
    assert get_fallback_model(MODEL_GEMINI_GROUNDING) == MODEL_GEMINI_TEXT
    assert get_fallback_model(MODEL_GEMINI_IMAGE) == MODEL_GEMINI_IMAGE_FALLBACK
    assert get_fallback_model("unknown-model") is None
