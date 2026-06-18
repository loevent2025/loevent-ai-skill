#!/usr/bin/env python3
"""skill-budget 结构化输出模型(pydantic v2)。

逐字对齐 engine/schemas/budget_schema.py 里 run.py 实际用到的 dict schema:
  budget_schema            → BudgetTextOut
  coefficients_schema      → CoefficientsOut
  generate_budget_schema   → GenerateBudgetOut(+ BudgetTaskItem)
  generate_budget_schema_en→ GenerateBudgetEnOut(+ BudgetTaskItemEn)

(budget_risk_check_schema 在本 skill 无调用点,故不建对应模型,避免引入死代码。)

字段名 / required / description / enum 与原 dict 逐字照搬:description 既是 genai
response_schema 给模型的产出指引,也是 JSON schema 的 property description,丢失会
掉产出质量,故全部照搬。原 required 字段不套 Optional;原 nullable/非 required 字段
设 Optional 默认 None。enum 用 typing.Literal 复刻(genai 原生吃 pydantic BaseModel)。

这些 model 类直接作为 llm.generate(response_schema=...) 传入,返回用
parse_structured(resp, ModelCls) 解析(.model_dump() 转 dict 或直接用实例)。
"""

from typing import List, Literal

from pydantic import BaseModel, Field


# ── budget_schema → 单 section 提取的纯文案输出 ──────────────────
class BudgetTextOut(BaseModel):
    text: str = Field(description="纯文案内容")


# ── coefficients_schema → 预算系数提取 ──────────────────────────
class CoefficientsOut(BaseModel):
    city_coeff: float = Field(description="城市系数，基于目标城市物价水平锚定")
    scale_coeff: float = Field(description="规模系数，根据活动人数确定")
    tier_coeff: float = Field(description="档次系数，根据活动定位（草根/中端/高端）确定")
    host_coeff: float = Field(description="主办方系数，根据主办方类型（社区/企业/政府）确定")
    contingency_rate: float = Field(description="应急预留比例，根据地区风险水平确定")
    cny_rate: float = Field(description="当地货币兑人民币汇率，即 1 单位当地货币等于多少 CNY")
    unit: str = Field(description="当地货币符号")
    region: Literal["europe", "new_york", "north_america", "southeast_asia", "kb"] = Field(
        description="活动所在地区"
    )


# ── generate_budget_schema → 生成分项预算(中文)──────────────────
class BudgetTaskItem(BaseModel):
    task: str
    budget_subject: Literal[
        "场地及空间",
        "餐饮服务",
        "技术与视听",
        "内容与演讲嘉宾",
        "人员劳务",
        "营销与传播",
        "物料与印刷品",
        "交通与住宿",
        "应急与其他",
    ] = Field(description="预算归属的一级类目，只能从以下9项中选择")
    low_estimate: float
    high_estimate: float
    unit: str = Field(description="货币符号")
    sponsorship_deductible: str = Field(
        description="是否可被赞助抵扣，只输出纯文字说明，禁止使用任何emoji或特殊符号。例如：'可抵扣'、'不可抵扣'、'部分可抵扣'。"
    )


class GenerateBudgetOut(BaseModel):
    task_list: List[BudgetTaskItem] = Field(description="每个任务一行")


# ── generate_budget_schema_en → 生成分项预算(英文)──────────────────
class BudgetTaskItemEn(BaseModel):
    task: str
    budget_subject: Literal[
        "Venue & Space",
        "Food & Beverage",
        "AV & Technology",
        "Content & Speakers",
        "Staffing & Labor",
        "Marketing & Communications",
        "Materials & Print",
        "Travel & Lodging",
        "Contingency & Miscellaneous",
    ] = Field(description="Primary budget category. Must be one of the 9 options below.")
    low_estimate: float
    high_estimate: float
    unit: str = Field(description="Currency code or symbol")
    sponsorship_deductible: str = Field(
        description="Whether the cost can be offset by sponsorship. Plain text only, no emoji or special characters. e.g. 'Deductible', 'Non-deductible', 'Partially deductible'."
    )


class GenerateBudgetEnOut(BaseModel):
    task_list: List[BudgetTaskItemEn] = Field(description="One row per task")
