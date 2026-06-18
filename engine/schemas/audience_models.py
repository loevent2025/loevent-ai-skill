#!/usr/bin/env python3
"""skill-audience 结构化输出模型(pydantic v2)。

对齐 engine/schemas/target_audience_schema.py 的 infer_audience_output_schema:
顶层 primary / secondary / extended 三个受众分层,每层共用同一结构
(audience 标签数组 + painpoint 痛点描述)。

字段名 / required / description 与旧 dict schema 逐字对齐:
description 既是 genai response_schema 给模型的产出指引,也是 JSON schema 的
property description,丢失会掉产出质量,故全部照搬。

约定:
  - 原 dict 三层均 required=["audience", "painpoint"],故两字段全部必填(不套 Optional)。
  - 顶层三层 required=["primary","secondary","extended"],故全部必填。
  - 该 model 类直接作为 llm.generate(response_schema=AudienceOutput) 传入
    (genai 原生吃 pydantic BaseModel);返回用 parse_structured(resp, AudienceOutput) 解析。
"""

from typing import List

from pydantic import BaseModel, Field


class AudienceSegment(BaseModel):
    audience: List[str] = Field(
        description="受众画像标签"
    )
    painpoint: str = Field(
        description="核心痛点描述，200字以内"
    )


class AudienceOutput(BaseModel):
    primary: AudienceSegment = Field(
        description="核心受众"
    )
    secondary: AudienceSegment = Field(
        description="次级受众"
    )
    extended: AudienceSegment = Field(
        description="扩展受众"
    )
