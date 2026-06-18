#!/usr/bin/env python3
"""skill-host-bio 结构化输出模型(pydantic v2)。

把 engine/schemas/host_profile_schema.py 里 skill-host-bio 用到的
self_description_polish_tool_schema(结构化润色:纯文案 text + 规范公司名 host_name)
改成 Pydantic BaseModel,直接作为 `llm.generate(response_schema=ModelCls)` 传入
(genai 原生吃 BaseModel),返回用 `parse_structured(resp, ModelCls)` 解析。

逐字对齐原 dict schema:
  - 字段名 / required / description 与原 dict 一字不差(description 既是 genai
    给模型的产出指引,也是 JSON schema 的 property description,丢失掉产出质量);
  - 原 required = ["text", "host_name"],两字段均为必填(`...`)。
"""

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────
# self_description_polish_tool_schema
# 结构化润色:把 grounding 调研文本整理成纯文案 + 规范公司名
# ─────────────────────────────────────────────────────────────
class SelfDescriptionPolish(BaseModel):
    text: str = Field(
        description="纯文案内容"
    )
    host_name: str = Field(
        description="公司/组织名称"
    )
