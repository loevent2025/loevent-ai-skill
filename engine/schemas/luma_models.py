#!/usr/bin/env python3
"""skill-luma 结构化输出模型(pydantic v2)。

逐字对齐 engine/schemas/schema.py 里本 skill 用到的两个 dict schema:
  - SocialPosterRcOut  ← social_poster_rc_schema(短/长文案最终出 text)
  - LongContent        ← long_content(长文案第一步 extract 的结构化字段)
    └── AgendaItem     ← long_content.agenda.items(子模型)

约定(与原 dict schema 逐字对齐):
  - 字段名 / required / description 照搬原 dict(description 既是 genai 给模型的产出
    指引,也是 JSON schema 的 property description,丢失会掉产出质量,故全部照搬)。
  - 原 dict required 里的字段 → 必填(无默认);其余(nullable/非 required)→ Optional 默认 None。
  - long_content 与 social_poster_rc_schema 的 required 都覆盖全部字段(无 nullable),
    故全部为必填。
  - 不改原 dict 文件(后端复用),本文件仅为单机 bundle 新建。

这些 model 类直接作为 llm.generate(response_schema=...) 传入(genai 原生吃 pydantic
BaseModel);返回用 parse_structured(resp, ModelCls) 解析。
"""

from typing import List

from pydantic import BaseModel, Field


class SocialPosterRcOut(BaseModel):
    text: str = Field(description="纯文案内容")


class AgendaItem(BaseModel):
    time: str = Field(
        description="时间段，如：'9:00 AM' 或 '9:00 AM - 11:00 AM'。",
    )
    activity: str = Field(
        description="活动内容描述，如：'Registration & Coffee' 或 'ZK Fundamentals Workshop (2 hours)'。",
    )


class LongContent(BaseModel):
    eventType: str = Field(
        description="活动类型，如：工作坊(Workshop)、峰会(Summit)、晚宴(Dinner)、聚会(Meetup)、黑客松(Hackathon)、圆桌(Roundtable)、论坛(Forum)、演示日(Demo Day)等。",
    )
    eventFormat: str = Field(
        description="活动形式，描述活动的互动方式，如：动手实践(Hands-on)、小组讨论(Breakout Sessions)、主题演讲(Keynote)、Panel讨论、结构化社交(Structured Networking)、混合形式等。",
    )
    coreProblem: str = Field(
        description="活动解决的核心痛点或抓住的机会，用于撰写Hook段落，建立相关性和紧迫感。例如：'大多数开发者想构建隐私保护应用，但不知道如何入门ZK电路和证明系统'。",
    )
    keyBenefits: List[str] = Field(
        description="参与者能获得的4-5个具体收益，每个收益需具体可衡量，包含详细说明。例如：['编写第一个ZK电路并理解基础原语', '比较SNARKs和STARKs证明系统，选择适合的方案', '与ZK研究者和协议工程师建立联系']。",
    )
    agenda: List[AgendaItem] = Field(
        description="活动议程时间线，包含各环节的时间和内容安排，需包含社交和休息环节。",
    )
    speakers: str = Field(
        description="嘉宾信息的整体描述，包含嘉宾姓名、职位、公司及具体成就，用于建立活动可信度。使用具体数据如ARR、融资额、用户数等。例如：'Led by the core engineering team from Protocol X, who've deployed ZK systems processing $500M+ in transactions. Guest speakers include researchers from Stanford and engineers from Coinbase.' 或 'Featuring founders from Company A ($10M ARR), Company B (acquired for $50M), and Company C (raised Series B from Sequoia). Plus fireside chat with prominent AI investor on what gets funded in 2025.'。",
    )
    luma_event_title: str = Field(
        description="获取核心命题部分的内容，不超过140个字符，如果超过进行总结提取",
    )
