#!/usr/bin/env python3
"""skill-init 抽取结构化输出模型(pydantic v2)。

把 engine/schemas/eventplanner_extractor_schema.py 里的 eventplanner_extract_schema
(dict 形式的 genai response_schema)逐字翻成 Pydantic BaseModel,供
llm.generate(response_schema=ExtractResult) 直接使用(genai 原生吃 BaseModel),
返回用 parse_structured(resp, ExtractResult) 校验解析。

约定(与原 dict schema 逐字对齐):
  - 字段名 / description 照搬原 dict(description 既是 genai 给模型的产出指引,
    也是 JSON schema 的 property description,丢失会掉产出质量,故全部照搬)。
  - 原 dict required 里的字段 → 必填(无默认);其余(nullable/非 required)→ Optional 默认 None。
  - 原 enum → typing.Literal(原样保留取值与顺序)。
  - 不改原 dict 文件(后端复用),本文件仅为单机 bundle 新建。
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class Basic(BaseModel):
    # 原 dict: nullable=True 但在 required 里 → 必填(可为 null);故 Optional 但无默认。
    title: Optional[str] = Field(
        description="活动标题/名称，如'2026 万向区块链全球峰会'",
    )
    theme: Optional[str] = Field(
        default=None,
        description="活动主题/核心议题，如'AI与区块链融合下的分布式商业'。从原文中提取活动的核心主题方向，与活动标题不同",
    )
    startTime: Optional[str] = Field(
        default=None,
        description="开始时间，格式 YYYY-MM-DDTHH:MM",
    )
    endTime: Optional[str] = Field(
        default=None,
        description="结束时间，格式 YYYY-MM-DDTHH:MM",
    )
    location: Optional[str] = Field(
        default=None,
        description="活动所在城市",
    )
    attendees: Optional[float] = Field(
        default=None,
        description="预计参会人数",
    )
    timezone: Optional[str] = Field(
        default=None,
        description="时区，如 Asia/Shanghai",
    )
    language: Literal["chinese", "english"] = Field(
        description="活动语言",
    )


class Host(BaseModel):
    name: Optional[str] = Field(
        default=None,
        description="组织/公司名称",
    )
    # 原 dict: enum 但 host 无 required → 非必填(Optional 默认 None)。
    industry: Optional[Literal["technology", "web3", "other"]] = Field(
        default=None,
        description="所属行业，仅限三个值：technology / web3 / other",
    )
    website: Optional[str] = Field(
        default=None,
        description="主办方网站",
    )
    profile: Optional[str] = Field(
        default=None,
        description="主办方简介",
    )


class Analysis(BaseModel):
    goal: Optional[str] = Field(
        default=None,
        description="活动目标与目的的完整描述。从原文全文中提取所有与活动目标、愿景、价值主张、战略意图、预期成果相关的内容，整合为详细段落。输出详细度与原文信息量成正比：原文丰富则详细输出（200-500字），原文简短则简短输出。",
    )
    content: Optional[str] = Field(
        default=None,
        description="活动内容设计概述",
    )
    partners: Optional[str] = Field(
        default=None,
        description="合作伙伴信息",
    )
    marketing: Optional[str] = Field(
        default=None,
        description="营销与推广策略",
    )


class Venue(BaseModel):
    id: str = Field(
        description="场地 ID，格式 rv-1, rv-2...",
    )
    text: str = Field(
        description="场地名称",
    )
    detail: Optional[str] = Field(
        default=None,
        description="场地详情",
    )


class Guest(BaseModel):
    id: str = Field(
        description="嘉宾 ID，格式 rg-1, rg-2...",
    )
    text: str = Field(
        description="嘉宾姓名",
    )
    detail: Optional[str] = Field(
        default=None,
        description="嘉宾职位与简介",
    )


class ExtractResult(BaseModel):
    basic: Basic = Field(
        description="活动基本信息",
    )
    host: Optional[Host] = Field(
        default=None,
        description="主办方信息",
    )
    analysis: Analysis = Field(
        description="活动分析",
    )
    venues: Optional[List[Venue]] = Field(
        default=None,
        description="推荐场地列表",
    )
    guests: Optional[List[Guest]] = Field(
        default=None,
        description="嘉宾/演讲者列表",
    )
    timeline: Optional[str] = Field(
        default=None,
        description="筹备时间线，按时间节点描述",
    )
    scene_type: Literal[
        "Large_exhibitions",
        "Business_conferences",
        "Hackathons",
        "Demo_days",
        "Technical_workshops",
        "Developer_meetups",
        "Community_day",
        "Cocktail",
        "Crossover",
    ] = Field(
        description="活动场景类型，根据活动内容判断最匹配的类型",
    )
    event_scale: Literal["small", "medium", "large"] = Field(
        description="活动规模：small(100人以内)、medium(100-300人)、large(300人以上)，根据参会人数或活动描述判断",
    )
    activate_type: Literal[
        "general", "community", "education", "investment", "technology"
    ] = Field(
        description="商业分类，根据活动内容判断最匹配的类别，无法判断时选择 general",
    )
    confirmed_audience: str = Field(
        description="目标受众/目标用户描述。如果原文明确提到目标受众则直接提取；如果未提到，则根据活动主题、内容、行业、规模等信息推断最可能的目标受众群体。",
    )
