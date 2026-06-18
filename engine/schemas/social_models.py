#!/usr/bin/env python3
"""skill-social 结构化输出模型(pydantic v2)。

逐字对齐 engine/schemas/socialpost_schema.py 的两个 dict schema:
  - SocialPosterRcOut         ← social_poster_rc_schema(x / community / 换行精修)
  - SocialPostXiaohongshuOut  ← socialpost_xiaohongshu_schema(小红书,带标题)

字段名 / required / description 与原 dict 逐字一致:description 既是 genai
response_schema 给模型的产出指引,也是 JSON schema 的 property description,丢失
会掉产出质量,故全部照搬。两个 schema 原 required 覆盖全部字段(无 nullable),
故全部为必填 str。

这些 model 类直接作为 llm.generate(response_schema=...) 传入(genai 原生吃 pydantic
BaseModel);返回用 parse_structured(resp, ModelCls) 解析。
"""

from pydantic import BaseModel, Field


class SocialPosterRcOut(BaseModel):
    text: str = Field(description="纯文案内容")


class SocialPostXiaohongshuOut(BaseModel):
    title: str = Field(description="标题")
    content: str = Field(description="正文内容")
