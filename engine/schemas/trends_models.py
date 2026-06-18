#!/usr/bin/env python3
"""skill-trends 综合卡片结构化输出模型(pydantic v2)。

对齐 engine/schemas/company_info_schema.py 里三个综合 schema:
  - industry_trends_schema    → IndustryTrendsOutput
  - topic_catalyst_schema     → TopicCatalystOutput
  - audience_pain_points_schema → AudiencePainPointsOutput

字段名 / required / description 与旧 dict schema 逐字对齐:
description 既是 genai response_schema 给模型的产出指引,也是 JSON schema 的
property description,丢失会掉产出质量,故全部照搬。

约定:
  - 三个 schema 结构相同:url(ARRAY, nullable, items STRING)+ summary(STRING),
    required 均为 ["url", "summary"]。
  - url 原 dict 既在 required 又 nullable=True(键必须出现、值可为 null),
    故用 Optional[List[str]] 且【不给默认值】—— 这样 model_json_schema() 里
    url 仍留在 required,同时允许值为 null,与旧 dict 语义逐字一致。
  - summary 必填普通 str。
  - 这些 model 类直接作为 llm.generate(response_schema=...) 传入(genai 原生吃
    pydantic BaseModel);返回用 parse_structured(resp, ModelCls) 解析。
"""

from typing import List, Optional

from pydantic import BaseModel, Field

_URL_DESC = (
    "来源内容中出现的所有相关URL链接。原样提取，不修改、不补全，"
    "搜不到则返回 null，禁止编造"
)


class IndustryTrendsOutput(BaseModel):
    url: Optional[List[str]] = Field(description=_URL_DESC)
    summary: str = Field(
        description="内容总结，整合以上所有信息的精炼概述，便于快速了解全貌，"
        "输出纯文本段落，禁止使用任何 Markdown 格式符号（如 #、##、-、*、|、```等），"
        "不分点、不加序号，以连贯的自然语言整段输出"
    )


class TopicCatalystOutput(BaseModel):
    url: Optional[List[str]] = Field(description=_URL_DESC)
    summary: str = Field(
        description="热点总结，综合以上所有热点事件的整体概述，提炼核心主题和关键趋势，"
        "便于快速把握近期动态全貌，输出纯文本段落，"
        "禁止使用任何 Markdown 格式符号（如 #、##、-、*、|、```等），"
        "不分点、不加序号，以连贯的自然语言整段输出"
    )


class AudiencePainPointsOutput(BaseModel):
    url: Optional[List[str]] = Field(description=_URL_DESC)
    summary: str = Field(
        description="痛点总结，综合所有痛点的核心洞察，提炼受众最关心的问题和共性需求，"
        "便于快速理解目标人群的心理状态，输出纯文本段落，"
        "禁止使用任何 Markdown 格式符号（如 #、##、-、*、|、```等），"
        "不分点、不加序号，以连贯的自然语言整段输出"
    )
