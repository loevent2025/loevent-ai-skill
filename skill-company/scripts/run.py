#!/usr/bin/env python3
"""
skill-company —— 主办方/竞品/趋势深度调研 + 三套策略方案(company)

对齐后端 company_info_search.company_info_search 的【完整调研管线】(去 Mongo/项目路由/track_timing):
  selection(场景分类,补 plan.event_scale/scene_type/activate_type)
  → 并行:主办方传承搜索(parallel_heritage_search) + 竞品列表与对标(search_competitors_list)
  → 综合洞察(synthesize_heritage)
  → 并行三套策略变体:品牌 DNA / 市场差异化 / 趋势前瞻(各自带预算估算 + 趋势卡:痛点/行业/话题)
  → 战略总结(generate_context_insight)
全程 Google Search grounding;每步搜索结果都过 verify_and_fix(check→fix)二次核查。

把后端 company_info_tools.py / company_info_trends.py 里需要的并行 search / synthesize /
variant / verify_and_fix 全部【内联进本脚本】,保持 skill 自包含、可独立分发。

infra 改动(只在基础设施,不动 AI 逻辑):
- Mongo find_one(user_events/host_profiles) → context_local.load_json("event"/"host");
- audience_data 从 audience.json 或 plan.audience 注入(必需,缺则报错先跑 loevent-audience);
- selection_prompt_know 的 DB 写(eventplanner_key.update_one)→ merge_into("plan", {...});
- 去 track_timing / 去项目路由;不记录用户信息,故删去 user_id/event_id 字段;
- selection_prompt 文本内联(避免改 engine/config);
- calculate_date_range 去 dateutil 依赖,改纯 stdlib。

降级:任一搜索/grounding 子任务失败不让整条管线崩(并行处统一用
asyncio.gather(return_exceptions=True),单步异常被降级为 None/空/跳过,主流程继续);
缺 GEMINI_API_KEY/网络全断才整体失败,由 run_skill_main 收口成结构化 {ok:false}。

用法:
    python skill-company/scripts/run.py                    # 读 event/host/audience(.json) + company_input.json
    python skill-company/scripts/run.py --max-competitors 2 \
        --goal product --objective "建立开发者心智"

产物:company.json 写入工作目录,并把核心结论 merge 进 plan.json;结构化结果打印到 stdout。
结果由 Claude 按 SKILL.md「结果呈现」整理成可读格式再给用户,不要直接甩 JSON。
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

_BUNDLE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.insert(0, _BUNDLE_ROOT)

from engine import (  # noqa: E402
    get_llm_client,
    load_yaml,
    safe_render,
    context_local,
    parse_structured,
    run_skill_main,
)
from engine.model_config import industry_map  # noqa: E402
from engine.schemas.company_models import (  # noqa: E402
    HostInsight,
    CompetitorsList,
    CompetitorBenchmarking,
    TrendCard,
    TrendCardForward,
    IndustryTrends,
    AudiencePainPoints,
    TopicCatalyst,
    SocialPosterRcOut,
    SelectionOut,
)

logger = logging.getLogger("loevent.company")

# 后端 company_info_tools/company_info_trends 的 module 常量(前两页 grounding 用,逐字保留)
SEARCH_MODULE = "company_search"            # ctx.search_module:汇总(structured)调用
GROUND_MODULE = "google_search_company_search"  # ctx.module:Google Search 调用

# 后端 company_info.yaml 已复制进 engine/config/,逐字一致
model_prompt = load_yaml("company_info.yaml")


# ─────────────────────────────────────────────────────────────
# 数据类(对齐后端 ai_config.CompanySearchContext)
# ─────────────────────────────────────────────────────────────
@dataclass
class CompanySearchContext:
    company_name: str
    theme: str
    attendees: int
    industry: str
    host_profile: str
    target_audience: Dict[str, Any]
    scene_type: str
    event_name: Optional[str] = None
    location: Optional[str] = None
    language: Optional[str] = None
    time_start: Optional[str] = None
    time_end: Optional[str] = None
    module: Optional[str] = GROUND_MODULE
    search_module: Optional[str] = SEARCH_MODULE


@dataclass
class SearchDimension:
    """趋势卡搜索维度配置(对齐后端 company_info_trends.SearchDimension)。"""
    name: str
    key: str
    focus_points: List[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────
# 薄封装:对齐后端 ai_gen.generate_google_search / generate_event_artice
# (后端走 providers.get_llm_client();此处走 engine 的同名单 Key client)
# ─────────────────────────────────────────────────────────────
async def generate_google_search(*, prompt: str, tool: str) -> str:
    """Google Search grounding 调用,返回自由文本。"""
    llm = get_llm_client()
    result = await llm.generate(module=tool, prompt=prompt, use_google_search=True)
    if result.used_google_search:
        logger.debug("grounding detected module=%s", tool)
    else:
        logger.debug("no grounding module=%s", tool)
    return result.text


async def generate_event_artice(*, prompt: str, tool: str,
                                config: Optional[Any] = None):
    """结构化(response_schema)生成。

    返回原始 LLMResponse(而非 .text),交调用方用 parse_structured(resp, Model)
    做健壮解析(容错截断/围栏 + finish_reason 提示)。config 可为 Pydantic
    BaseModel(genai 原生吃)或 dict schema。
    """
    llm = get_llm_client()
    return await llm.generate(module=tool, prompt=prompt, response_schema=config)


# ─────────────────────────────────────────────────────────────
# verify_and_fix(check → fix)—— 内联自 company_info_tools.py
# ─────────────────────────────────────────────────────────────
async def _step1_check(*, data: Any, tool: str, context: str = "") -> str:
    prompt = safe_render(
        model_prompt["CHECK_PROMPT"],
        content=json.dumps(data, ensure_ascii=False, indent=2),
        context=context,
    )
    llm = get_llm_client()
    response = await llm.generate(module=tool, prompt=prompt, use_google_search=True)
    return response.text


async def _step2_fix_one(*, field_val: Any, value: str, tool: str, context: str = "") -> str:
    prompt = safe_render(
        model_prompt["FIX_PROMPT"],
        data=field_val,
        issues_text=value,
        context=context,
    )
    llm = get_llm_client()
    response = await llm.generate(module=tool, prompt=prompt, use_google_search=True)
    return response.text


async def verify_and_fix(*, data: Any, tool: str, context: str = "") -> Dict[str, Any]:
    """两步核查:先 CHECK 出问题文本,无问题(NO_ISSUES)直接返回,否则 FIX 一次。"""
    issues_text = await _step1_check(data=data, tool=tool, context=context)
    if issues_text.strip("`").strip() == "NO_ISSUES":
        return {"data": data, "corrected": False}
    fixed_data = await _step2_fix_one(field_val=data, value=issues_text, tool=tool, context=context)
    return {"data": fixed_data, "corrected": True}


# ─────────────────────────────────────────────────────────────
# 主办方传承搜索(parallel_heritage_search)—— 内联
# ─────────────────────────────────────────────────────────────
async def parallel_heritage_search(content: CompanySearchContext):
    try:
        prompt = safe_render(
            model_prompt["search_heritage_dimension"],
            company_name=content.company_name,
            theme=content.theme,
            location=content.location,
            time_start=content.time_start,
            attendees=content.attendees,
            industry=content.industry,
            host_profile=content.host_profile,
            target_audience=content.target_audience,
            scene_type=content.scene_type,
        )
        result = await generate_google_search(prompt=prompt, tool=content.module)
        verified = await verify_and_fix(
            data=result,
            tool=content.module,
            context=f"{content.company_name}, {content.industry}",
        )
        search_prompt = safe_render(
            model_prompt["search_heritage_dimension_summary"],
            output_language=content.language,
            activity_content=verified["data"],
        )
        summary_result = await generate_event_artice(
            prompt=search_prompt, tool=content.search_module, config=HostInsight,
        )
        return parse_structured(summary_result, HostInsight).model_dump()
    except Exception as e:
        logger.error(f"parallel_heritage_search: {type(e).__name__}: {e}")
        return None


# ─────────────────────────────────────────────────────────────
# 竞品列表 + 单竞品对标(并行)—— 内联
# ─────────────────────────────────────────────────────────────
async def search_single_competitor(*, competitor_name: str,
                                    event_context: CompanySearchContext, introduction: str):
    prompt = safe_render(
        model_prompt.get("search_single_competitor"),
        competitor_name=competitor_name,
        introduction=introduction,
        company_name=event_context.company_name,
        theme=event_context.theme,
        attendees=event_context.attendees,
        location=event_context.location,
        time_start=event_context.time_start,
        industry=event_context.industry,
        host_profile=event_context.host_profile,
        target_audience=event_context.target_audience,
        scene_type=event_context.scene_type,
    )
    result = await generate_google_search(prompt=prompt, tool=event_context.module)
    verified = await verify_and_fix(
        data=result,
        tool=event_context.module,
        context=f"{competitor_name}, {event_context.industry}",
    )
    search_prompt = safe_render(
        model_prompt["search_single_competitor_summary"],
        competitor_name=competitor_name,
        introduction=introduction,
        scene_type=event_context.scene_type,
        theme=event_context.theme,
        output_language=event_context.language,
        competitor_raw_content=verified["data"],
    )
    summary_result = await generate_event_artice(
        prompt=search_prompt, tool=event_context.search_module,
        config=CompetitorBenchmarking,
    )
    return parse_structured(summary_result, CompetitorBenchmarking).model_dump()


async def parallel_competitor_search(*, competitors: List[Dict[str, str]],
                                     event_context: CompanySearchContext) -> List[dict]:
    """并行搜索所有竞品。

    用 asyncio.gather(return_exceptions=True):单个竞品搜索失败被降级跳过(不收进
    结果),而非整组崩。后端虽用 TaskGroup,但单机 skill 求鲁棒——一个竞品搜不到不该
    拖垮整条管线。
    """
    results = await asyncio.gather(
        *[
            search_single_competitor(
                competitor_name=c["name"],
                event_context=event_context,
                introduction=c.get("introduction", ""),
            )
            for c in competitors
        ],
        return_exceptions=True,
    )
    out: List[dict] = []
    for c, r in zip(competitors, results):
        if isinstance(r, Exception):
            logger.error(f"竞品 {c.get('name')!r} 对标失败,降级跳过: {type(r).__name__}: {r}")
            continue
        out.append(r)
    return out


async def search_competitors_list(*, content: CompanySearchContext,
                                  max_competitors: int = 2) -> List[dict]:
    # 阶段1:识别竞品列表
    prompt = safe_render(
        model_prompt["search_competitors_list"],
        company_name=content.company_name,
        host_profile=content.host_profile,
        max_competitors=max_competitors,
    )
    result = await generate_google_search(prompt=prompt, tool=content.module)
    search_prompt = safe_render(
        model_prompt["search_competitors_list_summary"],
        company_name=content.company_name,
        company_description=content.host_profile,
        competitors_raw_content=result,
    )
    summary_result = await generate_event_artice(
        prompt=search_prompt, tool=content.search_module, config=CompetitorsList,
    )
    parsed = parse_structured(summary_result, CompetitorsList).model_dump()
    competitors_raw = parsed.get("competitors", [])
    # 阶段2:每个竞品并行对标
    return await parallel_competitor_search(competitors=competitors_raw, event_context=content)


# ─────────────────────────────────────────────────────────────
# 综合洞察(synthesize_heritage)—— 内联
# ─────────────────────────────────────────────────────────────
async def synthesize_heritage(*, ctx: CompanySearchContext,
                              host_insight: dict, competitor_data: list):
    synthesis_prompt = safe_render(
        model_prompt.get("event_insight_summary"),
        company_name=ctx.company_name,
        theme=ctx.theme,
        attendees=ctx.attendees,
        industry=ctx.industry,
        host_profile=ctx.host_profile,
        target_audience=ctx.target_audience,
        host_insight_json=host_insight,
        competitor_data_json=competitor_data,
        output_language=ctx.language,
    )
    profile = await generate_event_artice(
        prompt=synthesis_prompt, tool=ctx.search_module, config=SocialPosterRcOut,
    )
    return parse_structured(profile, SocialPosterRcOut).text


# ─────────────────────────────────────────────────────────────
# 趋势卡搜索(company_info_trends.py)—— 内联
#  通用单维度搜索 + 并行多维度 + 综合;date_range 去 dateutil 依赖
# ─────────────────────────────────────────────────────────────
def _subtract_months(end: datetime, months: int) -> datetime:
    """纯 stdlib 的减月(替代 dateutil.relativedelta),日期溢出向月末夹紧。"""
    total = (end.year * 12 + (end.month - 1)) - months
    year, month = divmod(total, 12)
    month += 1
    # 处理目标月天数不足(如 3.31 - 1month → 2.28/29)
    if month == 12:
        next_month_first = datetime(year + 1, 1, 1)
    else:
        next_month_first = datetime(year, month + 1, 1)
    from datetime import timedelta
    last_day = (next_month_first - timedelta(days=1)).day
    return end.replace(year=year, month=month, day=min(end.day, last_day))


def calculate_date_range(*, months: int, time_end: str) -> str:
    end_date = datetime.strptime(time_end[:10], "%Y-%m-%d")
    start = _subtract_months(end_date, months)
    return f"{start.strftime('%Y年%m月')} 至 {end_date.strftime('%Y年%m月')}（近{months}个月）"


def _format_search_results(search_results: Dict[str, Any]) -> str:
    text = ""
    for _key, data in search_results.items():
        text += f"\n【{data['name']}】\n{data['content']}\n"
    return text


async def _search_dimension(*, dimension: SearchDimension, topic: str, industry: str,
                            region: str, date_range: str, module: str,
                            extra_context: str = "") -> Dict[str, Any]:
    """通用单维度搜索(逐字保留后端的研究员 prompt + verify_and_fix 二次核查)。"""
    focus_text = "\n".join([f"   - {p}" for p in dimension.focus_points])
    prompt = f"""
        # 角色
        你是一位严谨的行业信息研究员，擅长通过结构化推理找到高质量、可溯源的信息。

        # 搜索任务
        搜索 "{topic}" 在 "{industry}" 领域的【{dimension.name}】信息

        # 背景参数
        - 时间范围：{date_range}
        - 地区：{region if region else "全球"}
        {extra_context}

        # 搜索重点
        {focus_text}

        ---

        ## 执行要求

        以下三步必须按顺序完成。
        每步先写出推理过程，再执行操作，每步结束用一句话总结结论供下一步引用。

        ---

        ### 第一步：搜索前，想清楚搜索策略

        **想清楚第一件事：【{dimension.name}】这类信息，在互联网上最可能以什么形式存在？**

        思考：
        - 这类信息通常出现在哪些平台或媒体上？（官方公告、研究报告、新闻媒体、社交平台、学术论文等）
        - 权威来源是哪些？哪些来源的信息可信度最高？
        - 这类信息有哪些常见的关键词表达方式？中英文分别是什么？

        **想清楚第二件事：如何判断一条搜索结果是真实可信的，而不是过时的或无关的？**

        思考：
        - 时间是否在 {date_range} 范围内？
        - 来源是否权威可信？
        - 数据或结论是否有具体出处，还是泛泛而谈？

        **第一步结论：**
        总结：第一轮搜索词是什么，判断信息可信度的核心依据是什么，若第一轮无结果如何降级。

        ---

        ### 第二步：执行搜索，对每条结果做三层判断

        先回顾第一步结论，确认搜索词和判断标准，然后调用搜索工具。

        搜索上限 5 次，按以下顺序降级：
        - 第一轮：核心关键词 × {dimension.name} 维度词
        - 第二轮：叠加时间限定词或地区词（"{region if region else "全球"}"）
        - 第三轮：扩大范围兜底，使用更宽泛的行业词或英文搜索词

        每条结果完成以下三层判断，每层写出推理：

        **判断一：时效性是否符合要求？**
        是否在 {date_range} 范围内？若无明确时间标注，如何判断？

        **判断二：来源可信度如何？**
        来源属于官方/权威报告/主流媒体/社交平台中的哪种？
        是一手信息还是二手转载？有无具体数据佐证？

        **判断三：与【{dimension.name}】的相关程度如何？**
        是否直接回答了搜索重点中的问题？
        优先级：核心相关 / 部分相关 / 背景参考

        每轮搜索后统计：当前收录了多少条有效信息，是否需要继续下一轮。

        **第二步结论：**
        总结：最终收录了哪些信息，各自的可信度和相关程度，按优先级排序。

        ---

        ### 第三步：整理输出

        基于前两步结论，按以下格式输出所有收录信息：

        每条信息包含：
        - 核心内容（简明描述，保留关键数据）
        - 来源类型（官方 / 报告 / 媒体 / 社交平台）
        - 时间（具体日期或时间段）
        - 可信度（已确认 / 待验证）
        - 来源 URL

        若某条信息待验证，注明原因（如：来源为二手转载 / 无具体数据支撑 / 时间不明确）。

        若所有搜索轮次后仍无相关信息，输出：
        "No relevant information found"
        并列出执行过的搜索词和排除原因。
        """
    result = await generate_google_search(prompt=prompt, tool=module)
    context = f"话题: {topic}, 行业: {industry}, 维度: {dimension.name}"
    verified = await verify_and_fix(
        data={dimension.key: result}, tool=module, context=context,
    )
    if verified.get("corrected"):
        result = verified["data"]
    else:
        logger.info(f"✅ [{dimension.name}] 验证通过")
    return {"key": dimension.key, "name": dimension.name, "content": result}


async def _parallel_search_dimensions(*, dimensions: List[SearchDimension], topic: str,
                                      industry: str, region: str, date_range: str,
                                      module: str, extra_context: str = "") -> Dict[str, Any]:
    """并行搜索多个维度;单维度异常被吞,降级跳过(不崩整体)。"""
    tasks = [
        _search_dimension(
            dimension=dim, topic=topic, industry=industry, region=region,
            date_range=date_range, module=module, extra_context=extra_context,
        )
        for dim in dimensions
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    collected: Dict[str, Any] = {}
    for r in results:
        if isinstance(r, Exception):
            logger.error(f"搜索异常: {r}")
            continue
        collected[r["key"]] = {"name": r["name"], "content": r["content"]}
    return collected


async def _synthesize_results(*, synthesis_prompt: str, module: str,
                             config: Optional[Any]) -> Dict[str, Any]:
    result = await generate_event_artice(
        prompt=synthesis_prompt, tool=SEARCH_MODULE, config=config,
    )
    return parse_structured(result, config).model_dump()


async def search_industry_trends(*, ctx: CompanySearchContext):
    # language 兜底:后端 input 来自校验过的 DB(language 必填),单机版 input 是用户手写
    # event.json,可能漏字段;漏了就置空串,让 {language.upper()} 不崩、模型按上下文自判语言。
    topic, industry, language = ctx.theme, ctx.industry, (ctx.language or "")
    region = f"{ctx.location}所在的洲际"
    dimensions = [
        SearchDimension(name="讨论热度", key="heat", focus_points=[
            "搜索指数变化（Google Trends、百度指数等区域性搜索引擎）",
            "主流社交平台讨论量（Twitter/X、LinkedIn、Reddit、以及区域性平台）",
            "行业媒体报道频率（TechCrunch、Wired、VentureBeat 及区域头部科技媒体）",
            "相关会议/峰会/活动数量和规模（全球及区域性行业峰会）",
        ]),
        SearchDimension(name="主流观点", key="views", focus_points=[
            "全球及区域头部企业的战略布局和高管公开发言",
            "行业专家、知名投资人、意见领袖的分析判断",
            "国际咨询公司及投研机构的研究报告核心结论（Gartner、McKinsey、IDC等）",
            "行业内的主要争议点、技术路线分歧及不同阵营观点",
        ]),
        SearchDimension(name="趋势变化", key="trends", focus_points=[
            "全球及区域市场规模数据、增长率及预测",
            "近期投融资事件（金额、轮次、投资方、地域分布）",
            "主要国家/地区的政策风向（支持/监管/补贴/合规要求）",
            "关键技术突破、产品迭代进展及商业化落地案例",
        ]),
    ]
    try:
        date_range = calculate_date_range(months=2, time_end=ctx.time_start)
        extra_context = f"\n# 目标受众\n{ctx.target_audience}"
        search_results = await _parallel_search_dimensions(
            dimensions=dimensions, topic=topic, industry=industry, region=region,
            date_range=date_range, module=ctx.module, extra_context=extra_context,
        )
        results_text = _format_search_results(search_results)
        synthesis_prompt = f"""
            # 角色
            资深行业分析师，以数据严谨和洞察深刻著称

            # 任务
            生成【行业趋势洞察】卡片
            目标：提供社会证明和市场验证，帮助读者快速把握行业脉搏

            # 分析主题
            - 话题：{topic}
            - 行业：{industry}
            - 地区：{region or "全球"}

            # 搜索结果
            {results_text}

            # 输出结构（必须包含以下三个模块）

            ## 1.讨论热度
            - 当前话题的关注度和讨论活跃程度
            - 关键搜索指数、社交媒体声量、行业峰会/活动等热度指标
            - 与前期相比的热度变化（升温/降温/持平）

            ## 2.主流观点
            - 头部企业的战略布局和动向
            - 行业专家、投资人、研究机构的核心判断
            - 当前的主要共识与分歧点

            ## 3.趋势变化
            - 近期市场规模、增长数据或预测
            - 重要投融资事件或政策动向
            - 关键技术突破或商业化进展

            # 输出语言
            {language.upper()}

            # 要求
            - 每个模块用 2-3 个要点概括，简明扼要
            - 禁止编造数据或事件
            - summary 控制在 300 字/词以内
            - When outputting in English, use standard industry terms in English
            """
        card_data = await _synthesize_results(
            synthesis_prompt=synthesis_prompt, module=ctx.module, config=IndustryTrends,
        )
        card_data["results_text"] = results_text
        return card_data
    except Exception as e:
        logger.error(f"search_industry_trends: {type(e).__name__}: {e}", exc_info=True)
        return None


async def search_topic_catalyst(*, ctx: CompanySearchContext):
    # language 兜底:后端 input 来自校验过的 DB(language 必填),单机版 input 是用户手写
    # event.json,可能漏字段;漏了就置空串,让 {language.upper()} 不崩、模型按上下文自判语言。
    topic, industry, language = ctx.theme, ctx.industry, (ctx.language or "")
    region = f"{ctx.location}所在的国家"
    dimensions = [
        SearchDimension(name="重大新闻", key="news", focus_points=[
            "行业内的重大突发事件",
            "重要会议/峰会的核心议题和结论",
            "引发广泛讨论的标志性事件",
            "要求：具体日期 + 新闻标题 + 关键数据",
        ]),
        SearchDimension(name="政策动态", key="policy", focus_points=[
            "政府新发布的政策/法规/指导意见",
            "行业标准/规范的发布或更新",
            "监管动态和合规要求变化",
            "要求：发布日期 + 政策名称 + 发布机构 + 核心内容",
        ]),
        SearchDimension(name="企业动态", key="corporate", focus_points=[
            "头部企业的新产品发布/战略调整",
            "重大投融资/并购/上市事件",
            "重要人事变动/战略合作",
            "要求：公司名称 + 具体动作 + 日期",
        ]),
        SearchDimension(name="技术突破", key="tech", focus_points=[
            "新技术/新产品发布",
            "重要研究成果公布",
            "产品重大迭代升级",
            "要求：技术名称 + 发布方 + 创新点",
        ]),
    ]
    try:
        date_range = calculate_date_range(months=2, time_end=ctx.time_start)
        extra_context = f"\n# 目标受众\n{ctx.target_audience}"
        search_results = await _parallel_search_dimensions(
            dimensions=dimensions, topic=topic, industry=industry, region=region,
            date_range=date_range, module=ctx.module, extra_context=extra_context,
        )
        results_text = _format_search_results(search_results)
        synthesis_prompt = f"""
            # 角色
            资深新闻编辑，擅长捕捉热点并提炼传播点

            # 任务
            生成【话题引爆点】卡片
            目标：找到近30天内最新、最热的话题切入点，为内容创作提供素材

            # 分析主题
            - 话题：{topic}
            - 行业：{industry}
            - 地区：{region or "全球"}
            - 时间范围：近30天内

            # 搜索结果
            {results_text}

            # 输出结构（必须包含以下四个模块）

            ## 1. 重大新闻事件
            - 近30天内引发广泛关注的标志性事件
            - 格式：[日期] 事件标题 | 关键数据/影响 | 来源

            ## 2.政策动态
            - 近30天内发布的重要政策、法规、监管动向
            - 格式：[日期] 政策名称 | 发布机构 | 核心要点 | 来源

            ## 3.企业动态
            - 近30天内的产品发布、投融资、战略合作等重要事件
            - 格式：[日期] 公司名称 + 事件 | 关键数据（金额/估值等） | 来源

            ## 4.技术突破
            - 近30天内的新技术发布、研究成果、产品重大迭代
            - 格式：[日期] 技术/产品名称 | 发布方 | 核心创新点 | 来源

            # 输出语言
            {language.upper()}

            # 要求
            - 仅收录近30天内的事件，标注具体日期
            - 每个模块列出 1-3 条最具影响力的事件
            - 必须包含：具体标题 + 关键数据 + 权威来源名称
            - 权威来源包括：官方公告、Reuters、Bloomberg、政府官网、arXiv、顶级科技媒体等
            - 若某模块在搜索结果中无相关内容，标注「暂无相关动态」
            - 禁止编造事件、数据或来源
            - summary 控制在 300 字/词以内
            - When outputting in English, use standard industry terms in English
            """
        card_data = await _synthesize_results(
            synthesis_prompt=synthesis_prompt, module=ctx.module, config=TopicCatalyst,
        )
        card_data["results_text"] = results_text
        return card_data
    except Exception as e:
        logger.error(f"search_topic_catalyst: {type(e).__name__}: {e}", exc_info=True)
        return None


async def search_audience_pain_points(*, ctx: CompanySearchContext):
    # language 兜底:后端 input 来自校验过的 DB(language 必填),单机版 input 是用户手写
    # event.json,可能漏字段;漏了就置空串,让 {language.upper()} 不崩、模型按上下文自判语言。
    topic, industry, language = ctx.theme, ctx.industry, (ctx.language or "")
    region = ctx.location
    target_audience = ctx.target_audience
    dimensions = [
        SearchDimension(name="担忧与顾虑", key="concerns", focus_points=[
            "目标受众最担心、害怕、焦虑的事情",
            "做决策时的心理障碍和顾虑",
            "失败案例、负面经历引发的恐惧",
            "对未来/结果的不确定感",
        ]),
        SearchDimension(name="高频疑问", key="questions", focus_points=[
            "目标受众反复提出的问题",
            "新手入门时的常见困惑",
            "做选择/决策时的犹豫点",
        ]),
        SearchDimension(name="真实声音", key="voices", focus_points=[
            "用户原话、真实评论、口语化表达",
            "吐槽、抱怨、发泄的具体内容",
            "带有情绪色彩的表达（愤怒、失望、无奈、期待）",
            "搜索来源：社交媒体、产品评论区、社群讨论",
        ]),
    ]
    try:
        extra_context = f"\n# 目标受众\n{target_audience}"
        search_results = await _parallel_search_dimensions(
            dimensions=dimensions, topic=topic, industry=industry, region=region,
            date_range="", module=ctx.module, extra_context=extra_context,
        )
        results_text = _format_search_results(search_results)
        synthesis_prompt = f"""
            # 角色
            用户研究专家，擅长洞察用户心理和情感共鸣

            # 任务
            生成【受众痛点共鸣】卡片
            目标：精准击中目标人群的情感共鸣点

            # 分析主题
            - 话题：{topic}
            - 行业：{industry}
            - 目标受众：{target_audience}
            - 地区：{region or "全球"}

            # 搜索结果
            {results_text}

            # 输出语言
            {language.upper()}

            # 输出结构（必须包含以下四个模块）

            ## 1.高频痛点问题
            - 目标受众反复提及的核心问题和困惑
            - 按出现频率排序，列出 3-5 个最高频问题
            - 格式：问题 + 出现场景/背景

            ## 2.真实用户表达
            - 收集用户原话，保留口语化、情绪化特征
            - 格式：「原话内容」— 来源平台
            - 优先选择有代表性、有传播力的表达

            ## 3.情绪倾向分析
            - 识别主要情绪类型（焦虑/困惑/失望/期待/愤怒等）
            - 分析情绪背后的深层原因
            - 指出情绪最强烈的触发点

            ## 4.未被满足的需求
            - 现有方案无法解决的痛点
            - 用户期望与现实的差距
            - 被市场忽视的细分需求
            - 差评、投诉、流失的核心原因

            # 输出语言
            {language.upper()}

            # 要求
            - 聚焦真实用户声音，避免主观臆断
            - 引用真实表达时保留原始风格
            - 每个模块 2-4 个要点
            - 禁止编造用户原话或数据
            - summary 控制在 300 字/词以内
            - When outputting in English, use standard industry terms in English
            """
        card_data = await _synthesize_results(
            synthesis_prompt=synthesis_prompt, module=ctx.module, config=AudiencePainPoints,
        )
        card_data["results_text"] = results_text
        return card_data
    except Exception as e:
        logger.error(f"search_audience_pain_points: {type(e).__name__}: {e}", exc_info=True)
        return None


# ─────────────────────────────────────────────────────────────
# 三套策略变体 + 预算估算 —— 内联
# ─────────────────────────────────────────────────────────────
async def _estimate_budget(*, ctx: CompanySearchContext, vibe_content: dict) -> str:
    budget_prompt = safe_render(
        model_prompt["budget_estimation_prompt"],
        theme=ctx.theme,
        event_name=ctx.event_name,
        attendees=ctx.attendees,
        time_start=ctx.time_start,
        time_end=ctx.time_end,
        location=ctx.location,
        language=ctx.language,
        vibe_content=vibe_content,
    )
    return await generate_google_search(prompt=budget_prompt, tool=ctx.search_module)


async def generate_variant_brand_dna(*, ctx: CompanySearchContext, host_insight: dict):
    """Variant 1:基于品牌历史 DNA 生成方案。"""
    prompt = safe_render(
        model_prompt.get("generate_variant_brand_dna"),
        company_name=ctx.company_name,
        theme=ctx.theme,
        attendees=ctx.attendees,
        industry=ctx.industry,
        host_profile=ctx.host_profile,
        target_audience=ctx.target_audience,
        location=ctx.location,
        output_language=ctx.language,
        time_start=ctx.time_start,
        host_insight_json=host_insight,
    )
    result = await generate_event_artice(
        prompt=prompt, tool=ctx.search_module, config=TrendCard,
    )
    brand_dna_data = parse_structured(result, TrendCard).model_dump()
    brand_dna_data["budget"] = await _estimate_budget(ctx=ctx, vibe_content=brand_dna_data)
    return brand_dna_data


async def generate_variant_market_diff(*, ctx: CompanySearchContext,
                                       host_insight: dict, competitor_data: list):
    """Variant 2:基于竞品差异化生成方案。"""
    prompt = safe_render(
        model_prompt.get("generate_variant_market_diff"),
        company_name=ctx.company_name,
        theme=ctx.theme,
        attendees=ctx.attendees,
        industry=ctx.industry,
        host_profile=ctx.host_profile,
        target_audience=ctx.target_audience,
        location=ctx.location,
        output_language=ctx.language,
        time_start=ctx.time_start,
        host_insight_json=host_insight,
        competitor_data_json=competitor_data,
    )
    result = await generate_event_artice(
        prompt=prompt, tool=ctx.search_module, config=TrendCard,
    )
    market_diff_data = parse_structured(result, TrendCard).model_dump()
    market_diff_data["budget"] = await _estimate_budget(ctx=ctx, vibe_content=market_diff_data)
    return market_diff_data


async def generate_variant_trend_forward(*, ctx: CompanySearchContext, host_insight: dict):
    """Variant 3:基于趋势前瞻生成方案(先并行三张趋势卡:痛点/行业/话题)。

    三张趋势卡并行用 asyncio.gather(return_exceptions=True):任一张卡的子任务异常
    被降级为空 dict(而非让整组崩),主流程继续生成趋势前瞻方案。
    """
    pain_points_data, industry_trends_data, topic_catalyst_data = (
        await asyncio.gather(
            search_audience_pain_points(ctx=ctx),
            search_industry_trends(ctx=ctx),
            search_topic_catalyst(ctx=ctx),
            return_exceptions=True,
        )
    )
    for _name, _res in (
        ("audience_pain_points", pain_points_data),
        ("industry_trends", industry_trends_data),
        ("topic_catalyst", topic_catalyst_data),
    ):
        if isinstance(_res, Exception):
            logger.error(f"趋势卡 {_name} 失败,降级为空: {type(_res).__name__}: {_res}")

    pain_points_data = pain_points_data if isinstance(pain_points_data, dict) else {}
    industry_trends_data = industry_trends_data if isinstance(industry_trends_data, dict) else {}
    topic_catalyst_data = topic_catalyst_data if isinstance(topic_catalyst_data, dict) else {}

    trends_data = (
        pain_points_data.get("results_text"),
        industry_trends_data.get("results_text"),
        topic_catalyst_data.get("results_text"),
    )
    prompt = safe_render(
        model_prompt.get("generate_variant_trend_forward"),
        company_name=ctx.company_name,
        theme=ctx.theme,
        attendees=ctx.attendees,
        industry=ctx.industry,
        host_profile=ctx.host_profile,
        target_audience=ctx.target_audience,
        location=ctx.location,
        output_language=ctx.language,
        time_start=ctx.time_start,
        host_insight_json=host_insight,
        trends_json=trends_data,
    )
    result = await generate_event_artice(
        prompt=prompt, tool=ctx.search_module, config=TrendCardForward,
    )
    trend_forward_data = parse_structured(result, TrendCardForward).model_dump()
    trend_forward_data["budget"] = await _estimate_budget(ctx=ctx, vibe_content=trend_forward_data)

    return (
        trend_forward_data,
        pain_points_data.get("summary"),
        industry_trends_data.get("summary"),
        topic_catalyst_data.get("summary"),
    )


async def generate_context_insight(*, ctx: CompanySearchContext, host_insight: dict,
                                   competitor_data: list, brand_dna: dict,
                                   competitor: dict, trend_forward: dict):
    prompt = safe_render(
        model_prompt.get("generate_context_insight"),
        company_name=ctx.company_name,
        theme=ctx.theme,
        attendees=ctx.attendees,
        industry=ctx.industry,
        location=ctx.location,
        host_profile=ctx.host_profile,
        target_audience=ctx.target_audience,
        output_language=ctx.language,
        host_insight_json=host_insight,
        competitor_data_json=competitor_data,
        variant_brand_dna_json=brand_dna,
        variant_market_diff_json=competitor,
        variant_trend_forward_json=trend_forward,
    )
    result = await generate_event_artice(
        prompt=prompt, tool=ctx.search_module, config=SocialPosterRcOut,
    )
    return parse_structured(result, SocialPosterRcOut).text


# ─────────────────────────────────────────────────────────────
# 场景分类(selection_prompt_know)—— 内联(prompt 文本内联,不改 engine/config)
# 产出 event_scale/scene_type/activate_type → merge 进 plan
# ─────────────────────────────────────────────────────────────
_SELECTION_PROMPT = """You are an expert event classification specialist for the Web3 and AI industry. Based on
the event information provided by the user — event name: {{event_name}}, theme: {{theme}},
description: {{prompt}}, organization name: {{organization_name}}, location: {{location}},
attendee count: {{attendees}}, host profile: {{host_profile}} — perform accurate event
intent recognition and classification.

## Classification Rules

### 1. Scene Type (scene_type) — Required, choose one
Select the single best-matching scene:
- Technical_workshops: Workshop, hands-on, technical training, developer tutorial, Builder Session, tech sharing session
- Developer_meetups: Meetup, developer gathering, tech salon, offline exchange, community event, Networking, lightning talk
- Demo_days: Demo Day, Pitch Day, project pitch, fundraising roadshow, investor meeting, accelerator showcase, seed/angel round, VC matchmaking
- Hackathons: Hackathon, coding marathon, developer competition, Build Week, 48-hour challenge, Prize pool, Bounty, MVP development
- Business_conferences: Conference, business summit, industry forum, roundtable, B2B matchmaking, keynote, Panel discussion
- Large_exhibitions: Exhibition, Expo, trade show, summit, annual event, brand showcase, product launch, large event, sponsors
- Community_day: Community Day, open day, Cafe Session, co-working, developer space, member day, office hours, community hub
- Cocktail: Cocktail, reception, dinner, Gala Dinner, VIP dinner, After Party, awards dinner, wine tasting, Networking Dinner, Black Tie
- Crossover: Crossover, Art x Tech, music-tech, co-branded, cross-industry, immersive experience, creative market, pop-up, design week

### 2. Business Category (activate_type) — Required, choose one (default general when unclear)
- general: Industry basics, core technical principles, ecosystem introductions, trend analysis, beginner guides
- community: Meetups, AMAs, offline exchanges, Discord/Telegram management, Ambassador programs, community co-building
- education: Introductory courses, developer skill training, Bootcamps, workshops, certification, mentorship plans
- investment: Project pitch days, investor closed-door meetings, LP Days, deal flow sharing, accelerator Demo Days
- technology: Tech sharing, cutting-edge workshops, architecture discussions, Hackathons, code audit, open-source collaboration

### 3. City (city) — Optional, at most one. Return null if missing/online/not in list:
beijing, shanghai, shenzhen, hangzhou, hongkong, singapore, tokyo, bangkok, dubai,
newyork, sanfrancisco, losangeles, miami, austin, lasvegas, toronto, london, paris, berlin, amsterdam, barcelona

### 4. Event Scale (event_scale) — Required, choose one
- small: Under 100 attendees
- medium: 100–299 attendees (inclusive of 100)
- large: 300 or more attendees (inclusive of 300)
If attendee count is missing or cannot be parsed, infer from keywords. Default to large.

### 5. Language Detection
- chinese: User explicitly requests Chinese output
- english: User explicitly requests English output
- null: No explicit output language specified

## Output Requirements
Return strictly in JSON format with no explanations.
"""


async def selection_prompt_know(*, event_name, theme, attendees,
                               organization_name, host_profile, location, prompt=None):
    module_prompt = safe_render(
        _SELECTION_PROMPT,
        event_name=event_name,
        theme=theme,
        prompt=prompt,
        attendees=attendees,
        organization_name=organization_name,
        host_profile=host_profile,
        location=location,
    )
    llm = get_llm_client()
    result = await llm.generate(module="intent", prompt=module_prompt, response_schema=SelectionOut)
    return parse_structured(result, SelectionOut).model_dump()


# ─────────────────────────────────────────────────────────────
# 编排:对齐后端 company_info_search.company_info_search
# ─────────────────────────────────────────────────────────────
async def company_info_search(*, event: dict, host: dict, audience_data: dict,
                              max_competitors: int = 2) -> dict:
    # 1) 场景分类(补 plan.event_scale/scene_type/activate_type)
    response_module = await selection_prompt_know(
        event_name=event.get("event_name"),
        theme=event.get("theme"),
        attendees=event.get("attendees"),
        location=event.get("location"),
        organization_name=host.get("host_name"),
        host_profile=host.get("host_profile"),
    )
    selection_doc = {
        "event_scale": response_module.get("event_scale"),
        "scene_type": response_module.get("scene_type"),
        "activate_type": response_module.get("activate_type"),
    }
    # 后端写 eventplanner_key.update_one → 改 merge 进 plan
    context_local.merge_into("plan", {**selection_doc, "updatedAt": datetime.utcnow().isoformat()})

    ctx = CompanySearchContext(
        event_name=event.get("event_name"),
        company_name=host.get("host_name"),
        theme=event.get("theme"),
        attendees=event.get("attendees"),
        industry=industry_map.get(host.get("industry")),
        host_profile=host.get("host_profile"),
        target_audience=audience_data,
        location=event.get("location"),
        language=event.get("language"),
        time_start=event.get("time_start"),
        time_end=event.get("time_end"),
        scene_type=response_module.get("scene_type"),
    )

    # 2) 并行:主办方传承 + 竞品对标
    #    用 gather(return_exceptions=True):任一搜索子任务异常被降级(传承→None / 竞品→[]),
    #    不让整组崩;主流程带着可得数据继续。
    heritage_res, competitor_res = await asyncio.gather(
        parallel_heritage_search(content=ctx),
        search_competitors_list(content=ctx, max_competitors=max_competitors),
        return_exceptions=True,
    )
    if isinstance(heritage_res, Exception):
        logger.error(f"主办方传承搜索失败,降级为 None: {type(heritage_res).__name__}: {heritage_res}")
        company_data = None
    else:
        company_data = heritage_res
    if isinstance(competitor_res, Exception):
        logger.error(f"竞品对标搜索失败,降级为 []: {type(competitor_res).__name__}: {competitor_res}")
        competitor_data = []
    else:
        competitor_data = competitor_res

    # 3) 综合洞察
    event_insight_summary = await synthesize_heritage(
        ctx=ctx, host_insight=company_data, competitor_data=competitor_data,
    )

    # 4) 并行三套策略变体
    #    用 gather(return_exceptions=True):任一变体异常被降级(品牌DNA/市场差异化→{} ,
    #    趋势前瞻 4 元组→({},None,None,None)),不让整组崩;主流程继续做战略总结。
    brand_dna_res, competitor_res2, trend_forward_res = await asyncio.gather(
        generate_variant_brand_dna(ctx=ctx, host_insight=company_data),
        generate_variant_market_diff(
            ctx=ctx, host_insight=company_data, competitor_data=competitor_data),
        generate_variant_trend_forward(ctx=ctx, host_insight=company_data),
        return_exceptions=True,
    )
    if isinstance(brand_dna_res, Exception):
        logger.error(f"品牌DNA变体失败,降级为 {{}}: {type(brand_dna_res).__name__}: {brand_dna_res}")
        brand_dna = {}
    else:
        brand_dna = brand_dna_res
    if isinstance(competitor_res2, Exception):
        logger.error(f"市场差异化变体失败,降级为 {{}}: {type(competitor_res2).__name__}: {competitor_res2}")
        competitor = {}
    else:
        competitor = competitor_res2
    if isinstance(trend_forward_res, Exception):
        logger.error(f"趋势前瞻变体失败,降级为空: {type(trend_forward_res).__name__}: {trend_forward_res}")
        trend_forward, pain_points, industry_trends, topic_catalyst = {}, None, None, None
    else:
        trend_forward, pain_points, industry_trends, topic_catalyst = trend_forward_res

    # 5) 战略总结
    strategic_summary = await generate_context_insight(
        ctx=ctx, host_insight=company_data, competitor_data=competitor_data,
        brand_dna=brand_dna, competitor=competitor, trend_forward=trend_forward,
    )

    return {
        "strategic_summary": strategic_summary,
        "brand_dna": brand_dna,
        "competitor": competitor,
        "trend_forward": trend_forward,
        "strategic_details": {
            "event_insight_summary": event_insight_summary,
            "host_insight": company_data,
            "competitors": competitor_data,
        },
        "industry_trends": industry_trends,
        "topic_catalyst": topic_catalyst,
        "pain_points": pain_points,
        "selection": selection_doc,
    }


# ─────────────────────────────────────────────────────────────
# 输入解析:audience_data 必需(audience.json 或 plan.audience)
# ─────────────────────────────────────────────────────────────
def _resolve_audience() -> dict:
    """audience_data 必需:优先 audience.json,再退 plan.audience;都缺则报错。"""
    audience = context_local.load_json("audience")
    if not audience:
        plan = context_local.load_json("plan") or {}
        audience = plan.get("audience")
    if not audience:
        raise FileNotFoundError(
            "缺少目标受众画像(audience.json 或 plan.audience)。"
            "请先跑 loevent-audience 生成受众画像,再回来跑本工具。"
        )
    return audience


def _resolve_inputs(args) -> dict:
    data = context_local.load_json("company_input") or {}
    return {
        "max_competitors": (
            args.max_competitors
            if args.max_competitors is not None
            else data.get("max_competitors", 2)
        ),
        # event_goal/prompt_objective/GTMmatrix:与后端入参对齐保留(当前管线不消费,
        # 仅落地到 company.json 供下游/追溯;别让它们影响搜索逻辑)。
        "event_goal": args.goal or data.get("event_goal"),
        "prompt_objective": args.objective or data.get("prompt_objective"),
        "GTMmatrix": data.get("GTMmatrix"),
    }


async def _main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser(description="主办方/竞品/趋势深度调研 + 三套策略方案")
    p.add_argument("--max-competitors", dest="max_competitors", type=int,
                   help="竞品对标数量(默认 2)")
    p.add_argument("--goal", help="event_goal(留档用): product | ecosystem | brand")
    p.add_argument("--objective", help="一句话目标描述(留档用)")
    args = p.parse_args()

    event = context_local.load_json("event", required=True)
    host = context_local.load_json("host", required=True)
    audience_data = _resolve_audience()
    inp = _resolve_inputs(args)

    company = await company_info_search(
        event=event, host=host, audience_data=audience_data,
        max_competitors=inp["max_competitors"],
    )

    # 留档输入参数(便于追溯;不影响调研逻辑)
    company["_inputs"] = {
        "event_goal": inp["event_goal"],
        "prompt_objective": inp["prompt_objective"],
        "GTMmatrix": inp["GTMmatrix"],
        "max_competitors": inp["max_competitors"],
    }

    context_local.save_json("company", company)
    # 把核心结论 merge 进 plan(供下游 timeline/poster/socialpost 复用)
    context_local.merge_into("plan", {
        "company": {
            "strategic_summary": company.get("strategic_summary"),
            "brand_dna": company.get("brand_dna"),
            "competitor": company.get("competitor"),
            "trend_forward": company.get("trend_forward"),
            "industry_trends": company.get("industry_trends"),
            "topic_catalyst": company.get("topic_catalyst"),
            "pain_points": company.get("pain_points"),
        },
        **company.get("selection", {}),
    })

    out = {
        "ok": True,
        "workdir": str(context_local.workdir()),
        "written": ["company.json", "plan.json(merged)"],
        "company": company,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_skill_main(_main))
