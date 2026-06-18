"""
模型常量 + 映射表(单一来源 SSoT)

与后端 services/ai_tools/ai_utils/ai_config.py 顶部常量逐字一致。
模型升级 / doctor 探测降级,只改这一个文件。

注:grounding(Google Search)与所有纯文本调用一样,走默认文本模型
MODEL_GEMINI_TEXT —— 后端从未对带搜索的调用做 per-call 模型覆盖,
此处保持一致(全仓不存在 gemini-3.5)。
"""

# ── Gemini 文本(AI Studio);grounding 也走这个默认模型 ──────────
MODEL_GEMINI_TEXT           = "gemini-3-flash-preview"
MODEL_GEMINI_TEXT_FALLBACK  = "gemini-2.5-flash"

# ── Gemini 图像(AI Studio)──────────────────────────────────
MODEL_GEMINI_IMAGE          = "gemini-3-pro-image"        # GA endpoint (preview retires 2026-07-17)
MODEL_GEMINI_IMAGE_FALLBACK = "gemini-2.5-flash-image"

# ── 海报编辑专用(去文字效果优于 3 pro,故偏离默认)──
MODEL_POSTER_EDIT_IMAGE     = "gemini-2.5-flash-image"


# ==================== 映射表 ====================

language_map = {"chinese": "zh", "中文": "zh", "english": "en", "English": "en"}

industry_map = {
    "web3": "web3",
    "WEB 3": "web3",
    "technology": "ai_commercial",
    "AI & Technology": "ai_commercial",
    "other": "other",
    "General": "other",
}

# 海报风格 → style 知识库 md 文件名(与后端 ai_config.style_files 一致)
style_files = {
    "3drender": "3DRender.md", "algorithmicdesign": "AlgorithmicDesign.md",
    "blackgold": "BlackGold.md", "citysilhouette": "CitySilhouette.md",
    "cyberpunk": "Cyberpunk.md", "dataflow": "DataFlow.md",
    "generativeart": "GenerativeArt.md", "geometricgraphic": "GeometricGraphic.md",
    "glassmorphism": "GlassMorphism.md", "glitchart": "GlitchArt.md",
    "glowpixel": "GlowPixel.md", "gradientblur": "GradientBlur.md",
    "gridlayout": "GridLayout.md", "holographicglow": "HolographicGlow.md",
    "isometricfantasy": "IsometricFantasy.md", "keyboardview": "KeyboardView.md",
    "liquidglass": "LiquidGlass.md", "lowpoly": "LowPoly.md",
    "matrixflow": "MatrixFlow.md", "chromaticshards": "MetalGeometry.md",
    "midnightneon": "MidnightNeon.md", "minimalist": "Minimalist.md",
    "moonlightfantasy": "MoonlightFantasy.md", "neonlounge": "NeonLounge.md",
    "osaesthetics": "OSAesthetics.md", "photocomposite": "PhotoComposite.md",
    "pixelart": "PixelArt.md", "pixelrock": "PixelRock.md", "popart": "PopArt.md",
    "purplemystic": "PurpleMystic.md", "retroskeuomorphic": "RetroSkeuomorphic.md",
    "retrowave": "Retrowave.md", "pastelcyberpunk": "SoftNeon.md",
    "softshimmer": "SoftShimmer.md", "spacetech": "SpaceTech.md",
    "synthwave": "Synthwave.md", "techgradient": "TechGradient.md",
    "vaporwave": "Vaporwave.md",
}


def get_fallback_model(model: str):
    """返回失败时应重试的备用 model 名,无 fallback 则 None。"""
    if model == MODEL_GEMINI_IMAGE:
        return MODEL_GEMINI_IMAGE_FALLBACK
    if model == MODEL_GEMINI_TEXT:
        return MODEL_GEMINI_TEXT_FALLBACK
    return None
