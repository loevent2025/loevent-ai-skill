#!/usr/bin/env python3
"""
skill-trends —— 三维行业/话题/受众调研(grounding + 二次核查)

忠实搬运后端 module_tools/company_info_trends.py 的【三个调研入口】:
  - search_industry_trends   行业趋势洞察(讨论热度 / 主流观点 / 趋势变化)
  - search_topic_catalyst    话题引爆点(重大新闻 / 政策动态 / 企业动态 / 技术突破)
  - search_audience_pain_points 受众痛点共鸣(担忧顾虑 / 高频疑问 / 真实声音)

每个入口 = 多维度并行 grounding 搜索 → 逐维度 verify_and_fix 二次核查 → 综合 schema 出卡。
只改 infra(对齐 skill-audience / skill-poster 样板):
- Mongo find_one(user_events / host_profiles / pre_eventplanner / generated_fullplan)
  → context_local.load_json("event"/"host"/"plan");
- hot_new.update_one / 各 DB 写 → save_json("inspiration") + merge_into("plan", ...);
- 去掉 @track_timing、去掉 project 路由(engine 单 Key);user_id/event_id 用默认占位;
- verify_and_fix(原依赖 module_tools/company_info_tools.py)整段内联进本脚本,保持 skill 独立。

grounding / 网络失败要降级不崩:单维度失败只丢该维度,综合步失败该卡返回降级标记。

用法:
    python skill-trends/scripts/run.py                       # 三个维度全跑
    python skill-trends/scripts/run.py --dimension trends    # 只跑行业趋势
    python skill-trends/scripts/run.py --dimension catalyst --prompt "侧重出海"
    可选维度:trends(行业趋势) / catalyst(话题引爆点) / pain(受众痛点) / all(默认全跑)

产物:inspiration.json 写入工作目录,并 merge 进 plan.json;结构化结果打印到 stdout。
结果由 Claude 按 SKILL.md「结果呈现」整理后给用户,不要直接甩 JSON。
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dateutil.relativedelta import relativedelta

_BUNDLE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.insert(0, _BUNDLE_ROOT)

from engine import (  # noqa: E402
    get_llm_client,
    load_yaml,
    safe_render,
    context_local,
    parse_structured,
    run_skill_main,
    is_no_issues,
)
from engine.model_config import industry_map  # noqa: E402
from engine.schemas.trends_models import (  # noqa: E402
    IndustryTrendsOutput,
    TopicCatalystOutput,
    AudiencePainPointsOutput,
)

logger = logging.getLogger("loevent.trends")

# 维度调研走 grounding(Google Search);综合步走默认文本档(无搜索)。
# 后端用不同 module 名做 token 归账,单机版只用作日志标识,统一前缀即可。
SEARCH_MODULE = "trends_search"
SYNTH_MODULE = "trends_synthesis"


@dataclass
class SearchDimension:
    """搜索维度配置(逐字对齐后端 company_info_trends.SearchDimension)。"""

    name: str
    key: str
    focus_points: List[str]


# ─────────────────────────────────────────────────────────────
# 内联 verify_and_fix(搬自 module_tools/company_info_tools.py)
# CHECK_PROMPT / FIX_PROMPT 来自 engine/config/company_info.yaml;
# 两步都 use_google_search=True;step1 返回 "NO_ISSUES" 则跳过修正。
# 保持 skill 自包含,不反向依赖后端 module_tools。
# ─────────────────────────────────────────────────────────────
_model_prompt = load_yaml("company_info.yaml")


async def _step1_check(data: Dict[str, Any], module: str, context: str = "") -> str:
    prompt = safe_render(
        _model_prompt["CHECK_PROMPT"],
        content=json.dumps(data, ensure_ascii=False, indent=2),
        context=context,
    )
    llm = get_llm_client()
    response = await llm.generate(module=module, prompt=prompt, use_google_search=True)
    return response.text


async def _step2_fix_one(field: Any, value: str, module: str, context: str = "") -> str:
    prompt = safe_render(
        _model_prompt["FIX_PROMPT"],
        data=field,
        issues_text=value,
        context=context,
    )
    llm = get_llm_client()
    response = await llm.generate(module=module, prompt=prompt, use_google_search=True)
    return response.text


def _is_no_issues(issues_text: str) -> bool:
    """委托 engine.runtime.is_no_issues(trends/guests/company 共用,避免各自漂移)。"""
    return is_no_issues(issues_text)


async def verify_and_fix(
    data: Dict[str, Any], module: str, context: str = ""
) -> Dict[str, Any]:
    """二次核查 + 修正:返回 {"data": <str 维度正文>, "corrected": bool}。

    data 维度正文统一为字符串:无问题时回填原始正文(原 dict 的唯一值),
    有问题时回填 FIX 后的文本。两条路径 data 类型一致,避免上游拿到时而 dict
    时而 str 的不确定类型(原实现的类型不一致 bug)。
    """
    issues_text = await _step1_check(data=data, module=module, context=context)
    # data 形如 {dimension.key: <正文 str>};取出原始正文做统一回填基准
    original_text = next(iter(data.values())) if data else ""
    if _is_no_issues(issues_text):
        return {"data": original_text, "corrected": False}
    fixed_data = await _step2_fix_one(
        field=data, value=issues_text, module=module, context=context
    )
    return {"data": fixed_data, "corrected": True}


# ─────────────────────────────────────────────────────────────
# 内联 search_dimension(搬自 company_info_trends.py,canonical)
# 单维度:推理式 grounding 搜索 prompt → grounding 调用 → verify_and_fix。
# ─────────────────────────────────────────────────────────────
async def search_dimension(
    *,
    dimension: SearchDimension,
    topic: str,
    industry: str,
    region: str,
    date_range: str,
    module: str,
    extra_context: str = "",
) -> Dict[str, Any]:
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

    llm = get_llm_client()
    response = await llm.generate(module=module, prompt=prompt, use_google_search=True)
    result = response.text

    context = f"话题: {topic}, 行业: {industry}, 维度: {dimension.name}"
    verified = await verify_and_fix(
        data={dimension.key: result}, module=module, context=context
    )
    # verified["data"] 两条路径都是 str(无问题=原文,有问题=修正文),直接取用
    result = verified["data"]
    if not verified.get("corrected"):
        logger.info("[%s] 验证通过", dimension.name)

    return {"key": dimension.key, "name": dimension.name, "content": result}


async def parallel_search_dimensions(
    *,
    dimensions: List[SearchDimension],
    topic: str,
    industry: str,
    region: str,
    date_range: str,
    module: str,
    extra_context: str = "",
) -> Dict[str, Any]:
    """并行搜索多个维度;单维度异常只丢该维度,不影响整体(降级不崩)。"""
    tasks = [
        search_dimension(
            dimension=dim,
            topic=topic,
            industry=industry,
            region=region,
            date_range=date_range,
            module=module,
            extra_context=extra_context,
        )
        for dim in dimensions
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    collected: Dict[str, Any] = {}
    for r in results:
        if isinstance(r, Exception):
            logger.error("搜索维度异常: %s: %s", type(r).__name__, r)
            continue
        collected[r["key"]] = {"name": r["name"], "content": r["content"]}
    return collected


async def synthesize_results(
    *, synthesis_prompt: str, module: str, model_cls: type
) -> Dict[str, Any]:
    """综合搜索结果为结构化卡片(Pydantic schema 约束 → 已校验 dict)。

    genai 原生吃 BaseModel 作 response_schema;解析走共享内核 parse_structured
    (容错截断/围栏、MAX_TOKENS 提示),再 model_dump() 转 dict 供下游组装。
    """
    llm = get_llm_client()
    resp = await llm.generate(
        module=module, prompt=synthesis_prompt, response_schema=model_cls
    )
    return parse_structured(resp, model_cls).model_dump()


def format_search_results(search_results: Dict[str, Any]) -> str:
    """格式化搜索结果为文本(逐字对齐后端)。"""
    text = ""
    for _key, data in search_results.items():
        text += f"\n【{data['name']}】\n{data['content']}\n"
    return text


def calculate_date_range(months: int, time_end: str) -> str:
    """计算日期范围字符串(逐字对齐后端;time_end 形如 '2026-09-20 14:00')。"""
    end_date = datetime.strptime(time_end[:10], "%Y-%m-%d")
    start = end_date - relativedelta(months=months)
    return f"{start.strftime('%Y年%m月')} 至 {end_date.strftime('%Y年%m月')}（近{months}个月）"


# ─────────────────────────────────────────────────────────────
# 三个调研入口(搬自 company_info_trends.py,context 改入参注入)
# ─────────────────────────────────────────────────────────────
async def search_industry_trends(
    *, theme: str, location: str, industry: str, target_audience: Any,
    language: str, search_time: str, prompt: str = "",
) -> Optional[Dict[str, Any]]:
    topic = theme
    region = f"{location}所在的洲际"

    dimensions = [
        SearchDimension(
            name="讨论热度",
            key="heat",
            focus_points=[
                "搜索指数变化（Google Trends、百度指数等区域性搜索引擎）",
                "主流社交平台讨论量（Twitter/X、LinkedIn、Reddit、以及区域性平台）",
                "行业媒体报道频率（TechCrunch、Wired、VentureBeat 及区域头部科技媒体）",
                "相关会议/峰会/活动数量和规模（全球及区域性行业峰会）",
            ],
        ),
        SearchDimension(
            name="主流观点",
            key="views",
            focus_points=[
                "全球及区域头部企业的战略布局和高管公开发言",
                "行业专家、知名投资人、意见领袖的分析判断",
                "国际咨询公司及投研机构的研究报告核心结论（Gartner、McKinsey、IDC等）",
                "行业内的主要争议点、技术路线分歧及不同阵营观点",
            ],
        ),
        SearchDimension(
            name="趋势变化",
            key="trends",
            focus_points=[
                "全球及区域市场规模数据、增长率及预测",
                "近期投融资事件（金额、轮次、投资方、地域分布）",
                "主要国家/地区的政策风向（支持/监管/补贴/合规要求）",
                "关键技术突破、产品迭代进展及商业化落地案例",
            ],
        ),
    ]

    try:
        date_range = calculate_date_range(months=2, time_end=search_time)
        extra_context = f"\n# 目标受众\n{target_audience}"
        search_results = await parallel_search_dimensions(
            dimensions=dimensions, topic=topic, industry=industry, region=region,
            date_range=date_range, module=SEARCH_MODULE, extra_context=extra_context,
        )
        results_text = format_search_results(search_results)

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
            - 用户额外要求：{prompt}

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

        card_data = await synthesize_results(
            synthesis_prompt=synthesis_prompt, module=SYNTH_MODULE,
            model_cls=IndustryTrendsOutput,
        )
        card_data["results_text"] = results_text
        return card_data

    except Exception as e:
        logger.error("search_industry_trends %s: %s", type(e).__name__, e, exc_info=True)
        return None


async def search_topic_catalyst(
    *, theme: str, location: str, industry: str, target_audience: Any,
    language: str, search_time: str, prompt: str = "",
) -> Optional[Dict[str, Any]]:
    topic = theme
    region = f"{location}所在的国家"

    dimensions = [
        SearchDimension(
            name="重大新闻",
            key="news",
            focus_points=[
                "行业内的重大突发事件",
                "重要会议/峰会的核心议题和结论",
                "引发广泛讨论的标志性事件",
                "要求：具体日期 + 新闻标题 + 关键数据",
            ],
        ),
        SearchDimension(
            name="政策动态",
            key="policy",
            focus_points=[
                "政府新发布的政策/法规/指导意见",
                "行业标准/规范的发布或更新",
                "监管动态和合规要求变化",
                "要求：发布日期 + 政策名称 + 发布机构 + 核心内容",
            ],
        ),
        SearchDimension(
            name="企业动态",
            key="corporate",
            focus_points=[
                "头部企业的新产品发布/战略调整",
                "重大投融资/并购/上市事件",
                "重要人事变动/战略合作",
                "要求：公司名称 + 具体动作 + 日期",
            ],
        ),
        SearchDimension(
            name="技术突破",
            key="tech",
            focus_points=[
                "新技术/新产品发布",
                "重要研究成果公布",
                "产品重大迭代升级",
                "要求：技术名称 + 发布方 + 创新点",
            ],
        ),
    ]

    try:
        date_range = calculate_date_range(months=2, time_end=search_time)
        extra_context = f"\n# 目标受众\n{target_audience}"
        search_results = await parallel_search_dimensions(
            dimensions=dimensions, topic=topic, industry=industry, region=region,
            date_range=date_range, module=SEARCH_MODULE, extra_context=extra_context,
        )
        results_text = format_search_results(search_results)

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
            - 用户额外要求：{prompt}
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

        card_data = await synthesize_results(
            synthesis_prompt=synthesis_prompt, module=SYNTH_MODULE,
            model_cls=TopicCatalystOutput,
        )
        card_data["results_text"] = results_text
        return card_data

    except Exception as e:
        logger.error("search_topic_catalyst %s: %s", type(e).__name__, e, exc_info=True)
        return None


async def search_audience_pain_points(
    *, theme: str, location: str, industry: str, target_audience: Any,
    language: str, prompt: str = "",
) -> Optional[Dict[str, Any]]:
    topic = theme
    region = location

    dimensions = [
        SearchDimension(
            name="担忧与顾虑",
            key="concerns",
            focus_points=[
                "目标受众最担心、害怕、焦虑的事情",
                "做决策时的心理障碍和顾虑",
                "失败案例、负面经历引发的恐惧",
                "对未来/结果的不确定感",
            ],
        ),
        SearchDimension(
            name="高频疑问",
            key="questions",
            focus_points=[
                "目标受众反复提出的问题",
                "新手入门时的常见困惑",
                "做选择/决策时的犹豫点",
            ],
        ),
        SearchDimension(
            name="真实声音",
            key="voices",
            focus_points=[
                "用户原话、真实评论、口语化表达",
                "吐槽、抱怨、发泄的具体内容",
                "带有情绪色彩的表达（愤怒、失望、无奈、期待）",
                "搜索来源：社交媒体、产品评论区、社群讨论",
            ],
        ),
    ]

    try:
        extra_context = f"\n# 目标受众\n{target_audience}"
        search_results = await parallel_search_dimensions(
            dimensions=dimensions, topic=topic, industry=industry, region=region,
            date_range="", module=SEARCH_MODULE, extra_context=extra_context,
        )
        results_text = format_search_results(search_results)

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
            - 用户额外要求：{prompt}

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

        card_data = await synthesize_results(
            synthesis_prompt=synthesis_prompt, module=SYNTH_MODULE,
            model_cls=AudiencePainPointsOutput,
        )
        card_data["results_text"] = results_text
        return card_data

    except Exception as e:
        logger.error("search_audience_pain_points %s: %s", type(e).__name__, e, exc_info=True)
        return None


# ─────────────────────────────────────────────────────────────
# 上下文解析 + CLI
# ─────────────────────────────────────────────────────────────
_DIM_CHOICES = ("trends", "catalyst", "pain", "all")


def _resolve_target_audience(plan: Optional[Dict[str, Any]]) -> Any:
    """从 plan.json 取 target_audience(来自 skill-audience 的 audience.json)。

    后端从 pre_eventplanner.confirmed_audience / fullplan.ai_extracted 读;
    单机版改读上游 skill 落进 plan 的 audience。缺了不致命——传空让模型按主题降级。
    """
    if not plan:
        return ""
    # skill-audience merge 进 plan 的是 {"audience": {...}}
    aud = plan.get("audience")
    if aud:
        return aud
    # 兼容用户直接在 plan 里写 target_audience 的情况
    return plan.get("target_audience", "")


def _resolve_industry(host: Dict[str, Any]) -> str:
    """host.industry → industry_map(对齐后端 industry_map.get(..., 'other'))。"""
    return industry_map.get(host.get("industry"), "other")


async def _main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    p = argparse.ArgumentParser(description="三维行业/话题/受众调研(grounding + 二次核查)")
    p.add_argument(
        "--dimension", choices=_DIM_CHOICES, default="all",
        help="trends=行业趋势 / catalyst=话题引爆点 / pain=受众痛点 / all=全跑(默认)",
    )
    p.add_argument("--prompt", help="额外的用户方向描述(如 '侧重出海' / '聚焦中小企业')")
    args = p.parse_args()

    # 兜底读 templates 同名 input.json(可选,主要用于覆盖默认/额外方向)
    user_input = context_local.load_json("trends_input") or {}
    user_prompt = args.prompt or user_input.get("prompt", "")
    dimension = args.dimension or user_input.get("dimension", "all")

    event = context_local.load_json("event", required=True)
    host = context_local.load_json("host", required=True)
    plan = context_local.load_json("plan")  # 可选:含 skill-audience 的 audience

    theme = event.get("theme", "")
    location = event.get("location", "")
    language = event.get("language", "中文")
    search_time = event.get("time_start") or event.get("time_end") or ""
    industry = _resolve_industry(host)
    target_audience = _resolve_target_audience(plan)

    # search_time 用于行业趋势/话题引爆点的近 N 月时间窗;缺了就退化为"近期"
    if not search_time:
        logger.warning("event 缺 time_start/time_end,行业趋势/话题引爆点时间窗退化为'近期'。")
        search_time = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    run_trends = dimension in ("trends", "all")
    run_catalyst = dimension in ("catalyst", "all")
    run_pain = dimension in ("pain", "all")

    # 并行跑被选中的维度(任一失败只丢该卡,不影响其它)
    async with asyncio.TaskGroup() as tg:
        t_trends = tg.create_task(search_industry_trends(
            theme=theme, location=location, industry=industry,
            target_audience=target_audience, language=language,
            search_time=search_time, prompt=user_prompt,
        )) if run_trends else None
        t_catalyst = tg.create_task(search_topic_catalyst(
            theme=theme, location=location, industry=industry,
            target_audience=target_audience, language=language,
            search_time=search_time, prompt=user_prompt,
        )) if run_catalyst else None
        t_pain = tg.create_task(search_audience_pain_points(
            theme=theme, location=location, industry=industry,
            target_audience=target_audience, language=language,
            prompt=user_prompt,
        )) if run_pain else None

    industry_trends = t_trends.result() if t_trends else None
    topic_catalyst = t_catalyst.result() if t_catalyst else None
    pain_points = t_pain.result() if t_pain else None

    # 组装产物:每张卡 {summary, url, results_text(原始搜索文本,供下游 trend_forward 复用)}
    inspiration: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "topic": theme,
        "industry": industry,
        "language": language,
    }
    plan_patch: Dict[str, Any] = {}
    degraded: List[str] = []

    if run_trends:
        if industry_trends:
            inspiration["industry_trends"] = industry_trends
            plan_patch["industry_trends"] = {
                "summary": industry_trends.get("summary"),
                "url": industry_trends.get("url"),
            }
        else:
            degraded.append("trends")
    if run_catalyst:
        if topic_catalyst:
            inspiration["topic_catalyst"] = topic_catalyst
            plan_patch["topic_catalyst"] = {
                "summary": topic_catalyst.get("summary"),
                "url": topic_catalyst.get("url"),
            }
        else:
            degraded.append("catalyst")
    if run_pain:
        if pain_points:
            inspiration["audience_pain_points"] = pain_points
            plan_patch["audience_pain_points"] = {
                "summary": pain_points.get("summary"),
                "url": pain_points.get("url"),
            }
        else:
            degraded.append("pain")

    context_local.save_json("inspiration", inspiration)
    if plan_patch:
        context_local.merge_into("plan", plan_patch)

    out = {
        "ok": bool(plan_patch),
        "workdir": str(context_local.workdir()),
        "dimension": dimension,
        "written": ["inspiration.json"] + (["plan.json(merged)"] if plan_patch else []),
        "degraded": degraded,  # 这些维度 grounding/综合失败,已降级;非崩溃
        "inspiration": inspiration,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_skill_main(_main))
