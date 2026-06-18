#!/usr/bin/env python3
"""skill-guests 结构化输出模型(pydantic v2)。

对应 engine/schemas/schema.py 里 social_poster_rc_schema 的 pydantic 版本:
字段名 / required / description 与原 dict schema 逐字对齐——description 既是
genai response_schema 给模型的产出指引,也是 JSON schema 的 property description,
丢失会掉产出质量,故照搬。

约定:
  - text 为 str、必填(不套 Optional),与原 social_poster_rc_schema 的 required 一致。
  - 该 model 类直接作为 llm.generate(response_schema=GuestProfileOut) 传入(genai
    原生吃 pydantic BaseModel);返回用 parse_structured(resp, GuestProfileOut) 解析。
"""

from pydantic import BaseModel, Field


class GuestProfileOut(BaseModel):
    """对应 social_poster_rc_schema:嘉宾简介的纯文案输出。"""

    text: str = Field(description="纯文案内容")
