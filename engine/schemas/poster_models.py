#!/usr/bin/env python3
"""skill-poster 结构化输出模型(pydantic v2)。

对应 engine/schemas/schema.py 里的 poster_prompt_schema / reference_style_schema。
字段名 / required / description 与原 dict schema 逐字对齐:description 既是 genai
response_schema 给模型的产出指引,也是 JSON schema 的 property description,丢失会掉
产出质量,故全部照搬。

约定:
  - 原 schema 两个对象的所有字段都在 required 里、均非 nullable,故全部为必填 str
    (不套 Optional)。
  - 这些 model 类直接作为 llm.generate(response_schema=...) 传入(genai 原生吃
    pydantic BaseModel);返回用 parse_structured(resp, ModelCls) 解析。
"""

from pydantic import BaseModel, Field


class PosterPromptOut(BaseModel):
    """对应 poster_prompt_schema:10 节结构化海报生成 prompt,全部必填。"""

    section_1_aesthetic: str = Field(
        description="Mandatory prefix and chosen aesthetic direction that aligns with the event's theme and name. The aesthetic choice should feel naturally connected to what the event is about"
    )
    section_2_composition: str = Field(
        description="Dominant compositional strategy and spatial layout with specific angles/arrangement. The composition should reinforce the event theme's visual narrative. Include camera angles, rule of thirds, symmetry, or dynamic arrangements"
    )
    section_3_visual_elements: str = Field(
        description="Primary visual elements (2-4 max) that are semantically derived from the event name and theme as visual metaphors or symbolic representations. Each element must have a clear conceptual connection to the event's subject matter, not generic decorations. Describe shapes, objects, or focal points with specific attributes"
    )
    section_4_color_palette: str = Field(
        description="Precise color palette with hex-like specificity (e.g., #1A2B3C), gradient behavior, and contrast relationships. Include primary, secondary, and accent colors"
    )
    section_5_lighting_atmosphere: str = Field(
        description="Lighting and atmospheric effects that reinforce the event's theme and mood. Include light direction, intensity, shadows, fog, particles, etc. The atmosphere should evoke the feeling the event intends to create"
    )
    section_6_secondary_elements: str = Field(
        description="Secondary elements, textural overlays, or supporting visual effects. Include background details, patterns, textures, or decorative elements"
    )
    section_7_text_zones: str = Field(
        description="Text-ready zones with specific contrast description and hierarchy consideration for event details. Specify areas with high readability and contrast ratios"
    )
    section_8_mood_summary: str = Field(
        description="Overall mood and vibe summary derived from the event's theme and purpose. Capture the emotional tone and atmosphere in 1-2 sentences that reflect what the event aims to convey"
    )
    section_9_main_text_spec: str = Field(
        description="Main headline text specification. Format: 'Display the text \"[USER_THEME]\" prominently as the main headline in [font style], positioned at [location] with high contrast'. Include font weight, style, effects"
    )
    section_10_datetime_location_spec: str = Field(
        description='Date and location text specification. Format: \'Show "[USER_DATE]" and "[USER_LOCATION]" in smaller, clear typography positioned at [location], ensuring readability against the background\''
    )


class ReferenceStyleOut(BaseModel):
    """对应 reference_style_schema:从参考图抽取的可复用视觉风格指南。"""

    style_guide: str = Field(
        description="A complete visual style guide extracted from the reference image, covering: color palette (with hex values and ratios), typography style, layout and composition, visual effects (blur/glow/shadow/texture), decorative elements, and overall mood. Written as a reusable design directive in Markdown format."
    )
