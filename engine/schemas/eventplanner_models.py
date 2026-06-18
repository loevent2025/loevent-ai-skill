#!/usr/bin/env python3
"""skill-eventplanner 各节点结构化输出模型(pydantic v2)。

每个 NodeNOut = `section`(该章正文 Markdown)+ engine/schemas/schema.py 里
full_nodeN 的全部传话字段。字段名 / description 与 full_nodeN 逐字对齐:
description 既是 genai response_schema 给模型的产出指引,也是 JSON schema 的
property description,丢失会掉产出质量,故全部照搬。

约定:
  - 全部字段为 str、全部必填(不套 Optional),与旧 full_nodeN 的 required 一致。
  - section 的 description 来自旧 run.py 的 SCHEMA_NODE_N 那句各章中文。
  - 这些 model 类直接作为 llm.generate(response_schema=...) 传入(genai 原生吃
    pydantic BaseModel);返回用 model_validate_json(resp.text) 解析。
"""

from pydantic import BaseModel, Field


class Node1Out(BaseModel):
    section: str = Field(
        description="第一章:活动目标 / 背景 / 商业价值 的完整正文(Markdown,不要 HTML 标签)。"
    )
    eventType: str = Field(
        description="活动类型，例如开发者大会、技术沙龙、工作坊、生态见面会等"
    )
    eventTone: str = Field(
        description="活动基调或风格，例如正式、轻松、创意、科技、社区驱动或技术交流性质，用于体现活动整体氛围"
    )
    primaryAudience: str = Field(
        description="核心受众画像，如主要参与人群的角色、背景或兴趣点"
    )
    secondaryAudience: str = Field(
        description="次要受众画像，作为辅助目标人群"
    )
    shortTermGoals: str = Field(
        description="短期目标列表，例如活动当天希望实现的即时目标"
    )
    midTermGoals: str = Field(
        description="中期目标列表，例如活动结束后1周到1个月内想实现的结果"
    )
    longTermGoals: str = Field(
        description="长期目标列表，例如品牌建设、行业影响力提升等长期愿景"
    )
    organizerProfile: str = Field(
        description="组织方简介描述，包括组织背景、愿景、价值观等"
    )
    eventGoal: str = Field(
        description="活动整体目标，用于总结短中长期目标并呈现活动核心愿景"
    )
    twitterMetrics: str = Field(
        description="Twitter/X 相关传播指标，如目标曝光量、互动量、推文内容方向或传播策略"
    )


class Node2Out(BaseModel):
    section: str = Field(
        description="第二章:活动内容设计(受众画像 / 流程议程 / 嘉宾邀请)的完整正文(Markdown,不要 HTML 标签)。"
    )
    guestInfo: str = Field(
        description="嘉宾信息的详细描述，包括本次活动的嘉宾总览、重要嘉宾或特邀嘉宾的相关信息，以及与嘉宾相关的核心概况，可用于活动报告或流程规划。"
    )
    eventFlow: str = Field(
        description="活动流程列表，按顺序列出活动的各个环节和安排，例如演讲、嘉宾发言、互动、工作坊等"
    )
    targetAudience: str = Field(
        description="活动受众描述，包括目标参与人群的特征、背景、行业领域、职业角色或兴趣标签，例如AI创业者、技术开发者、投资人、产品经理等，用于明确活动定位和宣传方向。"
    )


class Node3Out(BaseModel):
    section: str = Field(
        description="第三章:场地筛选标准与推荐场地的完整正文(Markdown,不要 HTML 标签)。"
    )
    venueInfo: str = Field(
        description="具体参会地点的详细描述，包括活动举办的城市、场地名称或地址信息，用于活动组织、参会人员指引及物流安排。"
    )


class Node5Out(BaseModel):
    section: str = Field(
        description="第五章:合作与赞助(理想合作方画像)的完整正文(Markdown,不要 HTML 标签)。"
    )
    sponsorship: str = Field(
        description="理想合作方的详细画像，包括潜在赞助商或合作伙伴的类型、行业背景、合作意向及与活动的匹配度，用于活动合作洽谈和资源规划。"
    )


class Node6Out(BaseModel):
    section: str = Field(
        description="第六章:营销推广策略的完整正文(Markdown,不要 HTML 标签)。"
    )
    promotionMarketing: str = Field(
        description="推广信息的详细描述，包括活动宣传策略、渠道、推广内容或创意亮点，用于提升活动曝光、吸引目标受众及支持活动营销计划。"
    )
