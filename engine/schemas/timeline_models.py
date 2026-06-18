#!/usr/bin/env python3
"""skill-timeline 结构化输出模型(pydantic v2)。

对齐 engine/schemas/schema.py 的 timeline_schema:
顶层 tasks 数组,每个任务含 task_name / tag / startDate / endDate / priority。

字段名 / required / description / enum 与原 dict schema 逐字对齐:
原 timeline_schema 没有任何 description 字段,故这里也不补 description(逐字照搬)。

约定:
  - 原 dict 每个 task 的 required=["task_name","tag","startDate","endDate","priority"],
    五字段全部必填(不套 Optional)。
  - 顶层 required=["tasks"],故 tasks 必填。
  - enum 用 typing.Literal 复刻取值与顺序:
      tag      ∈ Marketing / Commercial / Venue / General
      priority ∈ P0 / P1 / P2 / P3
    (原 dict 里 priority 先写了一个 {"type":"NULL"} 又被同名 enum STRING 覆盖,
     dict 字面量取后者,故等价语义即 enum STRING 必填,这里照此实现。)
  - 该 model 类直接作为 llm.generate(response_schema=TimelineOutput) 传入
    (genai 原生吃 pydantic BaseModel);返回用 parse_structured(resp, TimelineOutput) 解析。
"""

from typing import List, Literal

from pydantic import BaseModel


class TimelineTask(BaseModel):
    task_name: str
    tag: Literal["Marketing", "Commercial", "Venue", "General"]
    startDate: str
    endDate: str
    priority: Literal["P0", "P1", "P2", "P3"]


class TimelineOutput(BaseModel):
    tasks: List[TimelineTask]
