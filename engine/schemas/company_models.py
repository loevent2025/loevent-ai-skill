#!/usr/bin/env python3
"""skill-company 各结构化输出模型(pydantic v2)。

把 engine/schemas/company_info_schema.py 里 skill-company 用到的 8 个 dict
response_schema 一对一改成 Pydantic BaseModel,直接作为
`llm.generate(response_schema=ModelCls)` 传入(genai 原生吃 BaseModel),
返回用 `parse_structured(resp, ModelCls)` 解析。

逐字对齐原 dict schema(model_json_schema() 与原 dict 等价):
  - 字段名 / required / description 与原 dict 一字不差(description 既是 genai
    给模型的产出指引,也是 JSON schema 的 property description,丢失掉产出质量);
  - **nullable 与 required 是两码事**:原 dict 里 `nullable: True` 且同时列在
    `required` 的字段(如各处的 url、host_insight 的 interaction/cohost),语义是
    「必须出现,但值可为 null」。对应 Pydantic = `Optional[...]` **且不给默认值**
    (无默认 → JSON schema 进 required;Optional → anyOf 含 null,允许 null)。
    只有原 dict 真·非 required 的字段才给 `default=None`;本 skill 用到的 8 个
    schema 里所有字段都在各自 required 里,故全部不给默认。
  - 数组项若原 items 带 description(如 url 项 '相关URL链接'、cohost 项 '身份标签'),
    用 `Annotated[str, Field(description=...)]` 作 list 项类型保留该项级描述;
  - 对象型数组项(host_insight 的 interaction/location item)单独建子模型。

注意:company_info_schema.py 里 host_insight_schema 被定义了两次,import 实际拿到的
是第二个(含 url 字段、nullable、小写 type)的定义,本文件照第二个(生效的那个)建模。
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field
from typing_extensions import Annotated


# ─────────────────────────────────────────────────────────────
# host_insight_schema(生效定义:company_info_schema.py 第 100-153 行)
# 自身公司的历史活动信息
# ─────────────────────────────────────────────────────────────
class HostInsightTextItem(BaseModel):
    text: str = Field(
        description="格式：'互动形式名称 (效果标签)'，效果标签为：高转化/高传播/低参与/高互动/常规"
    )


class HostInsightLocationItem(BaseModel):
    text: str = Field(
        description="格式：场地类型"
    )


# host_insight.cohost / url 的数组项带项级 description
_HostInsightCohostItem = Annotated[str, Field(description="身份标签")]
_HostInsightUrlItem = Annotated[str, Field(description="活动相关URL链接")]


class HostInsight(BaseModel):
    interaction: Optional[List[HostInsightTextItem]] = Field(
        description="过往核心互动形式，每项包含形式名称和效果标签。必须基于搜索到的真实活动，搜不到则返回 null，禁止编造",
    )
    location: Optional[List[HostInsightLocationItem]] = Field(
        description="过往场地偏好，每项包含场地类型。必须基于搜索到的真实活动，搜不到则返回 null，禁止编造",
    )
    cohost: Optional[List[_HostInsightCohostItem]] = Field(
        description="历史活动中出现的嘉宾/合作方身份标签。必须基于搜索到的真实活动，搜不到则返回 null，禁止编造",
    )
    url: Optional[List[_HostInsightUrlItem]] = Field(
        description="历史活动内容中出现的所有URL链接。必须基于输入内容中真实存在的URL，搜不到则返回 null，禁止编造",
    )


# ─────────────────────────────────────────────────────────────
# competitors_list_schema(只返回 2 个竞品,每个只有名字和介绍)
# ─────────────────────────────────────────────────────────────
class CompetitorListItem(BaseModel):
    name: str = Field(
        description="竞品公司名称",
    )
    introduction: str = Field(
        description="一段话介绍该竞品公司",
    )


class CompetitorsList(BaseModel):
    competitors: List[CompetitorListItem] = Field(
        description="2个竞品公司",
        min_length=2,
        max_length=2,
    )


# ─────────────────────────────────────────────────────────────
# competitor_benchmarking_schema(竞品公司历史活动分析)
# ─────────────────────────────────────────────────────────────
_CompetitorUrlItem = Annotated[str, Field(description="活动相关URL链接")]


class CompetitorBenchmarking(BaseModel):
    title: Optional[str] = Field(
        description="公司名字[产品名字]。如果未搜索到真实活动数据则返回 null",
    )
    interaction: Optional[str] = Field(
        description="互动形式：活动的互动方式、风格特点及参与者体验描述。必须基于搜索到的真实活动，搜不到则返回 null，禁止编造",
    )
    location: Optional[str] = Field(
        description="场地选择：活动场地偏好、选址逻辑及品牌调性描述。必须基于搜索到的真实活动，搜不到则返回 null，禁止编造",
    )
    guest_composition: Optional[str] = Field(
        description="嘉宾构成：演讲嘉宾类型、层级及生态合作方描述。必须基于搜索到的真实活动，搜不到则返回 null，禁止编造",
    )
    url: Optional[List[_CompetitorUrlItem]] = Field(
        description="搜索结果中出现的所有活动相关URL链接。原样提取，不修改、不补全，搜不到则返回 null，禁止编造",
    )


# ─────────────────────────────────────────────────────────────
# trend_card_schema(策略变体卡:品牌 DNA / 市场差异化)
# ─────────────────────────────────────────────────────────────
class TrendCard(BaseModel):
    title: str = Field(
        description="趋势前瞻卡片标题，如 '黑客之光'"
    )
    slogan: str = Field(
        description="趋势口号，一句话概括活动调性，如 '让最纯粹的代码，在最有质感的空间里共鸣。'"
    )
    location: str = Field(
        description="建议场地类型，如 '工业风改造画廊 / 私密地下酒窖'"
    )
    interaction: str = Field(
        description="核心互动方式，如 'Lightning Talk + 深度代码围炉会'"
    )
    cohost_guest: str = Field(
        description="建议 CO-HOST / GUEST 方向，如 '头部开源项目维护者 / 技术播客主理人'"
    )


# ─────────────────────────────────────────────────────────────
# trend_card_forward_schema(趋势前瞻策略变体卡,比 trend_card 多 url)
# ─────────────────────────────────────────────────────────────
_TrendForwardUrlItem = Annotated[str, Field(description="相关URL链接")]


class TrendCardForward(BaseModel):
    title: str = Field(
        description="趋势前瞻卡片标题，如 '黑客之光'"
    )
    slogan: str = Field(
        description="趋势口号，一句话概括活动调性，如 '让最纯粹的代码，在最有质感的空间里共鸣。'"
    )
    location: str = Field(
        description="建议场地类型，如 '工业风改造画廊 / 私密地下酒窖'"
    )
    interaction: str = Field(
        description="核心互动方式，如 'Lightning Talk + 深度代码围炉会'"
    )
    cohost_guest: str = Field(
        description="建议 CO-HOST / GUEST 方向，如 '头部开源项目维护者 / 技术播客主理人'"
    )
    url: Optional[List[_TrendForwardUrlItem]] = Field(
        description="来源内容中出现的所有相关URL链接。原样提取，不修改、不补全，搜不到则返回 null，禁止编造",
    )


# ─────────────────────────────────────────────────────────────
# 趋势卡通用 url 项(industry_trends / audience_pain_points / topic_catalyst)
# ─────────────────────────────────────────────────────────────
_TrendCardUrlItem = Annotated[str, Field(description="相关URL链接")]


# ─────────────────────────────────────────────────────────────
# industry_trends_schema(行业趋势洞察卡)
# ─────────────────────────────────────────────────────────────
class IndustryTrends(BaseModel):
    url: Optional[List[_TrendCardUrlItem]] = Field(
        description="来源内容中出现的所有相关URL链接。原样提取，不修改、不补全，搜不到则返回 null，禁止编造",
    )
    summary: str = Field(
        description="内容总结，整合以上所有信息的精炼概述，便于快速了解全貌，输出纯文本段落，禁止使用任何 Markdown 格式符号（如 #、##、-、*、|、```等），不分点、不加序号，以连贯的自然语言整段输出",
    )


# ─────────────────────────────────────────────────────────────
# audience_pain_points_schema(受众痛点共鸣卡)
# ─────────────────────────────────────────────────────────────
class AudiencePainPoints(BaseModel):
    url: Optional[List[_TrendCardUrlItem]] = Field(
        description="来源内容中出现的所有相关URL链接。原样提取，不修改、不补全，搜不到则返回 null，禁止编造",
    )
    summary: str = Field(
        description="痛点总结，综合所有痛点的核心洞察，提炼受众最关心的问题和共性需求，便于快速理解目标人群的心理状态，输出纯文本段落，禁止使用任何 Markdown 格式符号（如 #、##、-、*、|、```等），不分点、不加序号，以连贯的自然语言整段输出",
    )


# ─────────────────────────────────────────────────────────────
# topic_catalyst_schema(话题引爆点卡)
# ─────────────────────────────────────────────────────────────
class TopicCatalyst(BaseModel):
    url: Optional[List[_TrendCardUrlItem]] = Field(
        description="来源内容中出现的所有相关URL链接。原样提取，不修改、不补全，搜不到则返回 null，禁止编造",
    )
    summary: str = Field(
        description="热点总结，综合以上所有热点事件的整体概述，提炼核心主题和关键趋势，便于快速把握近期动态全貌，输出纯文本段落，禁止使用任何 Markdown 格式符号（如 #、##、-、*、|、```等），不分点、不加序号，以连贯的自然语言整段输出",
    )


# ─────────────────────────────────────────────────────────────
# social_poster_rc_schema —— 纯文案输出(原在后端 schema.py;company 综合步用)
# ─────────────────────────────────────────────────────────────
class SocialPosterRcOut(BaseModel):
    text: str = Field(description="纯文案内容")


# ─────────────────────────────────────────────────────────────
# selection_schema —— 意图分类(场景/分类/城市/规模/语言;原在后端 schema.py)
#   city / language 为 required 且 nullable:Optional 无默认 → 留在 required 同时接受 null。
# ─────────────────────────────────────────────────────────────
class SelectionOut(BaseModel):
    scene_type: Literal[
        "Large_exhibitions", "Business_conferences", "Hackathons", "Demo_days",
        "Technical_workshops", "Developer_meetups", "Community_day", "Cocktail", "Crossover",
    ] = Field(description="活动场景类型，必选一个")
    activate_type: Literal[
        "general", "community", "education", "investment", "technology",
    ] = Field(description="商业分类，必选一个，无法判断时选择general")
    city: Optional[Literal[
        "beijing", "shanghai", "shenzhen", "hangzhou", "hongkong", "singapore", "tokyo",
        "bangkok", "dubai", "newyork", "sanfrancisco", "losangeles", "miami", "austin",
        "lasvegas", "toronto", "london", "paris", "berlin", "amsterdam", "barcelona",
    ]] = Field(description="活动城市，可选")
    event_scale: Literal["small", "medium", "large"] = Field(
        description="活动规模：small(100人以内)、medium(100-300人)、large(300人以上)"
    )
    language: Optional[Literal["english", "chinese"]]
