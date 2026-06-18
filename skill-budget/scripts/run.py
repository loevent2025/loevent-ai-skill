#!/usr/bin/env python3
"""
skill-budget —— 为活动估算分项预算(任务级 low/high + 类目 + 赞助可抵扣)

对齐后端 budget.info_budget 的【生成路径】,但:
- 上下文不查 Mongo,改读本地 event.json / host.json / plan.json(由 skill-init / 上游 skill 生成);
- 任何 DB 写 → 改成 save_json("budget") + merge_into("plan", {...});
- 去掉 @track_timing 装饰器、去掉 project 路由(engine 单 key);user_id/event_id 不传(用默认)。

【相对后端的简化(按 v1 单机版方案)】
- 不联网下载历史预算 Excel(避免 openpyxl / aiohttp / csv):historical_budgets 始终为空;
- 系数(汇率/城市/规模/档次)走 grounding 实时搜索(对齐后端 process_db_data);
  汇率/系数搜索失败时**降级**:用一组中性系数(全 1.0、cny_rate=1),不让 skill 崩;
- 静态预算模板优先读本地 config/budget/{region}.json(已随 bundle 复制,用 config_path 解析);
- 解析 plan 里的全案 HTML(node2/node3/node5/node6)需要 bs4:bs4 设为可选 import,
  缺则跳过 HTML 解析这段,改走 ai_extracted / 空提取源。

【两条提取源(对齐后端双源)】
- source == "ai_extracted":从 plan.ai_extracted(content/marketing/venues/partners)取提取源(to_model_tool);
- 其它(ai_generated / 缺省):从 plan.html_content 解析全案 HTML(to_planner_tool)。
- 两者都没有:仍能跑——提取源为空,纯靠静态模板 + 系数生成基线预算。

产物:budget.json 写入工作目录,并 merge 进 plan.json;结构化结果打印到 stdout。
agent 按 SKILL.md「结果呈现」把它整理成可读格式再给用户,不要直接甩 JSON。

用法:
    python skill-budget/scripts/run.py                       # 全新生成(读 event/host/plan)
    python skill-budget/scripts/run.py --regenerate "整体压到 8 万以下,餐饮减 30%"  # 在已有预算上按指令调整
"""

import argparse
import asyncio
import json
import math
import os
import re
import sys

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
from engine.config_loader import config_path  # noqa: E402
from engine.schemas.budget_models import (  # noqa: E402
    BudgetTextOut,
    CoefficientsOut,
    GenerateBudgetOut,
    GenerateBudgetEnOut,
)

BUDGET_TOOL = "budget_tool"
GOOGLE_SEARCH_BUDGET_TOOL = "google_search_budget_tool"

SOURCE_AI_EXTRACTED = "ai_extracted"

# 降级/跳过的结构化备注:凡是吞掉的非致命异常(缺 bs4、系数 grounding 失败、场地
# 搜索失败、提取子任务失败)都记一条,随产出一起返回,避免只 print stderr 静默吞掉。
_NOTES: list = []


def _note(msg: str) -> None:
    """记录一条降级备注(同时 print stderr 方便本地观察)。"""
    _NOTES.append(msg)
    print(f"[warn] {msg}", file=sys.stderr)

# 语言感知 schema(对齐后端 BUDGET_SCHEMA_MAP;dict schema → Pydantic 模型类)
BUDGET_SCHEMA_MAP = {
    "chinese": GenerateBudgetOut,
    "中文": GenerateBudgetOut,
    "english": GenerateBudgetEnOut,
    "English": GenerateBudgetEnOut,
}

# 全案 HTML 标题 → node key(对齐后端 ai_config.eventplanner_titles,内联自包含)
EVENTPLANNER_TITLES = {
    "chinese": {
        "node_1": "活动目的",
        "node2": "活动内容设计",
        "node3": "地点选择",
        "node4": "筹备时间线",
        "node5": "合作伙伴",
        "node_6": "营销与推广",
        "node_7": "成本与预算",
    },
    "english": {
        "node_1": "Event Goals",
        "node2": "Content Design",
        "node3": "Venue Selection",
        "node4": "Preparation Timeline",
        "node5": "Partnerships",
        "node_6": "Marketing & Promotion",
        "node_7": "Cost & Budget",
    },
}


# ── 共用 helper(内联自 ai_gen,保持 skill 独立)──────────────────
async def _generate_event_artice(prompt, tool, config=None):
    """对齐后端 generate_event_artice:纯文本/结构化生成,返回 .text。

    用于下游再喂回 prompt 的裸文本场景(提取结果 / 校验结果);需要解析成
    结构化 dict 的场景请用 _generate_structured(走 parse_structured 健壮解析)。
    """
    llm = get_llm_client()
    resp = await llm.generate(module=tool, prompt=prompt, response_schema=config)
    return resp.text


async def _generate_structured(prompt, tool, model_cls) -> dict:
    """结构化生成 + 健壮解析:llm.generate(response_schema=ModelCls) → parse_structured。

    genai 原生吃 Pydantic BaseModel 作为 response_schema;parse_structured 负责
    剥围栏 / 容错截断 JSON,失败抛带 finish_reason 的清晰异常(交 run_skill_main 兜底)。
    返回 model_dump() 后的 dict。
    """
    llm = get_llm_client()
    resp = await llm.generate(module=tool, prompt=prompt, response_schema=model_cls)
    return parse_structured(resp, model_cls).model_dump()


async def _generate_google_search(prompt, tool):
    """对齐后端 generate_google_search:带 Google Search grounding,返回 .text。"""
    llm = get_llm_client()
    resp = await llm.generate(module=tool, prompt=prompt, use_google_search=True)
    return resp.text


def check_and_fix_escapes(text: str) -> str:
    """检查文本里是否存在字面量转义字符,有则修复,并格式化【】标记。

    内联自后端 host_profile_tools.check_and_fix_escapes(语言后处理)。
    """
    if not isinstance(text, str):
        return text
    patterns = {"\\n": "\n", "\\r": "\r", "\\t": "\t"}
    fixed = text
    for esc, real in patterns.items():
        fixed = fixed.replace(esc, real)
    first = fixed.find("【")
    if first != -1:
        after_first = fixed[first + 1:]
        after_first = re.sub(r"】", "】\n", after_first)
        after_first = re.sub(r"【", "\n【", after_first)
        fixed = fixed[: first + 1] + after_first
    return fixed


# ── 静态预算模板 + 系数调整(对齐后端 _load_budget_tasks / adjust_budget)──
_BUDGET_TASKS_CACHE = {}


def _load_budget_tasks(region: str) -> dict:
    """加载指定 region 的静态预算模板 JSON(路径改用 config_path,随 bundle 走)。"""
    region = region or "kb"
    if region not in _BUDGET_TASKS_CACHE:
        p = config_path("budget", f"{region}.json")
        if not p.exists():
            p = config_path("budget", "kb.json")  # 兜底
        with open(p, encoding="utf-8") as f:
            _BUDGET_TASKS_CACHE[region] = json.load(f)
    return _BUDGET_TASKS_CACHE[region]


def adjust_budget(items: list, coefficients: dict) -> list:
    """按系数把静态模板的 low/high 折算到目标地区货币(对齐后端 adjust_budget)。"""
    multiplier = (
        coefficients.get("city_coeff", 1)
        * coefficients.get("scale_coeff", 1)
        * coefficients.get("tier_coeff", 1)
        * coefficients.get("host_coeff", 1)
    )
    cny_rate = coefficients.get("cny_rate", 1) or 1
    adjusted = []
    for item in items:
        new_item = item.copy()
        if item.get("low") is not None:
            new_item["low"] = math.ceil(item["low"] * multiplier / cny_rate)
        if item.get("high") is not None:
            new_item["high"] = math.ceil(item["high"] * multiplier / cny_rate)
        adjusted.append(new_item)
    return adjusted


# ── 系数提取(对齐后端 process_db_data;grounding 失败则降级)──────
_NEUTRAL_COEFFICIENTS = {
    "city_coeff": 1.0,
    "scale_coeff": 1.0,
    "tier_coeff": 1.0,
    "host_coeff": 1.0,
    "contingency_rate": 0.1,
    "cny_rate": 1.0,
    "unit": "CNY",
    "region": "kb",
}


async def process_db_data(event: dict, host: dict) -> tuple:
    """搜索系数 → 结构化提取 → 按 region 取静态模板并折算。

    返回 (db_data, coefficients)。任何网络/解析失败 → 中性系数 + kb 模板,降级不崩。
    """
    budget_data = load_yaml("budget.yaml")
    try:
        coefficients_info = safe_render(
            budget_data["budget_coefficients"],
            event_name=event.get("event_name"),
            location=event.get("location"),
            attendees=event.get("attendees"),
            industry=host.get("industry"),
            host_profiles=host.get("host_name"),
        )
        coefficients_text = await _generate_google_search(
            prompt=coefficients_info, tool=GOOGLE_SEARCH_BUDGET_TOOL
        )

        coefficients_prompt = f"""你是一位活动预算数据提取专家。请从以下文本中提取活动预算相关的系数信息，结构化输出。

        ## 输入文本
        {coefficients_text}

        ## 活动地点
        {event.get("location")}

        ## 任务要求
        1. 根据活动地点判断所属地区（region），分类规则如下：
           - "new_york"：纽约市及周边地区
           - "north_america"：除纽约外的北美地区（美国、加拿大、墨西哥等）
           - "europe"：欧洲地区
           - "southeast_asia"：东南亚地区
           - "kb"：不属于以上任何地区
        2. 从文本中提取各项系数值（city_coeff、scale_coeff、tier_coeff、host_coeff、contingency_rate）
        3. 提取当地货币代码（ISO 4217）、货币符号及兑人民币汇率
        4. 在 reasoning 中用一句话概括各系数的取值依据，纯文本输出，禁止使用任何 Markdown 格式符号"""

        coefficients = await _generate_structured(
            prompt=coefficients_prompt, tool=BUDGET_TOOL, model_cls=CoefficientsOut
        )
    except Exception as e:  # grounding / 解析失败 → 降级
        _note(f"系数搜索/提取失败({type(e).__name__}: {e}),改用中性系数(全 1.0,cny_rate=1)降级,"
              "金额未按城市/规模/档次折算,仅供量级参考。")
        coefficients = dict(_NEUTRAL_COEFFICIENTS)

    budget_tasks = _load_budget_tasks(coefficients.get("region"))
    db_data = adjust_budget(items=budget_tasks.get("items", []), coefficients=coefficients)
    return db_data, coefficients


# ── 单 section 预算提取(对齐后端 _extract_single_budget)──────────
async def _extract_single_budget(section_id: str, content: str, location: str) -> dict:
    budget_data = load_yaml("budget.yaml")
    budget_prompt = safe_render(
        budget_data["budget_get_tasks"],
        eventplanner_content=content,
        location=location,
    )
    result = await _generate_event_artice(
        prompt=budget_prompt, tool=BUDGET_TOOL, config=BudgetTextOut
    )
    return {"id": section_id, "result": result}


# ── 场地搜索(对齐后端 _run_venue_search;失败降级为 None)────────────
async def _venue_search(event: dict, venue_data):
    if not venue_data:
        return None
    budget_data = load_yaml("budget.yaml")
    try:
        venue_search_prompt = safe_render(
            budget_data["venue_search"],
            time_start=event.get("time_start"),
            time_end=event.get("time_end"),
            attendees=event.get("attendees"),
            venue_data=venue_data,
        )
        return await _generate_google_search(
            prompt=venue_search_prompt, tool=GOOGLE_SEARCH_BUDGET_TOOL
        )
    except Exception as e:
        _note(f"场地搜索失败({type(e).__name__}: {e}),跳过场地补充(场地相关预算未做实时锚定)。")
        return None


# ── 全案 HTML 解析(对齐后端 parse_html_sections;bs4 可选)──────────
def parse_html_sections(html_content: str) -> dict:
    """把全案 HTML 按章节标题映射成 {node-key: html}。

    返回空 {} 有两种语义,务必区分:
      - 无 html_content / 真的没有可匹配章节 → 正常空,不记 note;
      - 缺 bs4 依赖,根本没法解析 → 记一条明确 note(产出会缺 HTML 提取源,
        需装 bs4 或改走 ai_extracted),避免和"真的空"混淆。
    """
    if not html_content:
        return {}
    try:
        from bs4 import BeautifulSoup  # 可选依赖:缺则跳过 HTML 解析
    except Exception:
        _note(
            "未安装 bs4,有 html_content 但无法解析全案 HTML 提取源"
            "(产出仅靠静态模板+系数,质量下降);请 pip install beautifulsoup4 或改用 ai_extracted 源。"
        )
        return {}

    soup = BeautifulSoup(html_content, "html.parser")
    sections = soup.find_all("div", class_="section")

    title_to_key = {}
    for lang in ("chinese", "english"):
        for key, title in EVENTPLANNER_TITLES[lang].items():
            title_to_key[title.lower().strip()] = key

    result = {}
    for section in sections:
        h2 = section.find("h2")
        if not h2:
            continue
        raw_title = h2.get_text(strip=True)
        cleaned = re.sub(r"^[一二三四五六七八九十\d]+[、.\s]+", "", raw_title).strip()
        matched_key = title_to_key.get(cleaned.lower())
        if matched_key is None:
            for norm_title, key in title_to_key.items():
                if norm_title in cleaned.lower() or cleaned.lower() in norm_title:
                    matched_key = key
                    break
        if matched_key is not None:
            content_div = section.find("div", class_="section-content")
            html_str = str(content_div) if content_div else str(section)
            text = content_div.get_text(strip=True) if content_div else section.get_text(strip=True)
            if text:
                result[matched_key.replace("_", "")] = html_str
    return result


# ── 共用:提取 + 校验 + 生成(to_planner_tool / to_model_tool 的公共尾部)──
async def _extract_validate_generate(
    *, event: dict, host: dict, extract_tasks: list, event_planner_source: str,
    venue_data, partners_content,
):
    budget_data = load_yaml("budget.yaml")

    async def _run_budget_extraction():
        results = await asyncio.gather(*extract_tasks, return_exceptions=True)
        final = []
        for r in results:
            if isinstance(r, Exception):
                _note(f"预算提取子任务失败({type(r).__name__}: {r}),该 section 提取源缺失。")
            else:
                final.append(r)
        return final

    final_results, (db_data, _coeff), venue_search_data = await asyncio.gather(
        _run_budget_extraction(),
        process_db_data(event=event, host=host),
        _venue_search(event, venue_data),
    )

    check_final_results_prompt = safe_render(
        budget_data["budget_task_validator"],
        event_name=event.get("event_name"),
        event_type=event.get("theme"),
        location=event.get("location"),
        attendees=event.get("attendees"),
        industry=host.get("industry"),
        host_profiles=host.get("host_name"),
        time_start=event.get("time_start"),
        time_end=event.get("time_end"),
        event_planner=event_planner_source,
        task_list=final_results,
    )
    check_final_results = await _generate_event_artice(
        prompt=check_final_results_prompt, tool=BUDGET_TOOL
    )

    generate_prompt = safe_render(
        budget_data["generate_budget_prompt"],
        time_start=event.get("time_start"),
        time_end=event.get("time_end"),
        user_tasks=check_final_results,
        db_tasks=db_data,
        historical_budgets=None,  # 简化:不联网下载历史 Excel
        attendee_count=event.get("attendees"),
        Partner_content=partners_content if partners_content else None,
        venue_search_data=venue_search_data,
    )

    if partners_content:
        info_excel_path = config_path("budget", "info_excel.md")
        if info_excel_path.exists():
            generate_prompt = f"{generate_prompt}\n\n{info_excel_path.read_text(encoding='utf-8')}"

    results = await _generate_google_search(
        prompt=generate_prompt, tool=GOOGLE_SEARCH_BUDGET_TOOL
    )
    return results


# ── 提取源 A:全案 HTML(对齐后端 to_planner_tool)────────────────
async def to_planner_tool(*, event, host, html_content: dict):
    allowed_keys = {"node2", "node6"}
    target_ids = [k for k in html_content.keys() if k in allowed_keys]

    extract_tasks = []
    for section_id in target_ids:
        content = html_content.get(section_id)
        if content is None:
            continue
        extract_tasks.append(
            _extract_single_budget(section_id, content, event.get("location"))
        )

    if html_content.get("node3"):
        venue_data = html_content["node3"]
    else:
        venue_data = None

    event_planner_source = "\n\n".join(
        html_content[sid] for sid in target_ids if html_content.get(sid)
    )
    partners_content = html_content.get("node5")

    return await _extract_validate_generate(
        event=event, host=host, extract_tasks=extract_tasks,
        event_planner_source=event_planner_source,
        venue_data=venue_data, partners_content=partners_content,
    )


# ── 提取源 B:结构化 ai_extracted(对齐后端 to_model_tool)──────────
async def to_model_tool(*, event, host, ai_extracted: dict):
    extract_sources = {
        "node2": ai_extracted.get("content"),
        "node6": ai_extracted.get("marketing"),
    }
    extract_tasks = []
    for section_id, content in extract_sources.items():
        if not content:
            continue
        extract_tasks.append(
            _extract_single_budget(section_id, content, event.get("location"))
        )

    venues = ai_extracted.get("venues") or {}
    venue_data = None
    if isinstance(venues, dict):
        venue_data = venues.get("confirmed") or venues.get("recommended")

    event_planner_source = "\n\n".join(
        v for v in [ai_extracted.get("content"), ai_extracted.get("marketing")] if v
    )
    partners_content = ai_extracted.get("partners")

    return await _extract_validate_generate(
        event=event, host=host, extract_tasks=extract_tasks,
        event_planner_source=event_planner_source,
        venue_data=venue_data, partners_content=partners_content,
    )


# ── 调整已有预算(对齐后端 regeneration_prompt 分支)──────────────────
async def regenerate_budget(*, event, prior_budget_tasks, regeneration_prompt):
    budget_data = load_yaml("budget.yaml")
    adjust_prompt = safe_render(
        budget_data["adjust_budget_prompt"],
        user_input=regeneration_prompt,
        budget_tasks=prior_budget_tasks,
    )
    return await _generate_structured(
        prompt=adjust_prompt, tool=BUDGET_TOOL,
        model_cls=BUDGET_SCHEMA_MAP.get(event.get("language"), GenerateBudgetOut),
    )


# ── entry:info_budget(对齐后端 info_budget,DB → 本地 JSON)───────
async def info_budget(*, event, host, plan, regeneration_prompt=None):
    source = (plan or {}).get("source", "")

    # 调整路径:在已有预算上按用户指令改
    if regeneration_prompt:
        prior = (plan or {}).get("budget") or context_local.load_json("budget") or {}
        prior_budget_tasks = (
            prior.get("budget_data", {}).get("groups")
            or prior.get("task_list")
            or prior
        )
        return await regenerate_budget(
            event=event, prior_budget_tasks=prior_budget_tasks,
            regeneration_prompt=regeneration_prompt,
        )

    # 全新生成:按 source 选提取源(双源)
    if source == SOURCE_AI_EXTRACTED and (plan or {}).get("ai_extracted"):
        results = await to_model_tool(
            event=event, host=host, ai_extracted=plan.get("ai_extracted", {})
        )
    else:
        html_content = parse_html_sections((plan or {}).get("html_content", ""))
        results = await to_planner_tool(event=event, host=host, html_content=html_content)

    # 把生成的预算报告结构化(语言感知 schema)
    budget_data = load_yaml("budget.yaml")
    structure_prompt = safe_render(
        budget_data["structure_api_search"],
        results=results,
        language=event.get("language"),
    )
    return await _generate_structured(
        prompt=structure_prompt, tool=BUDGET_TOOL,
        model_cls=BUDGET_SCHEMA_MAP.get(event.get("language"), GenerateBudgetOut),
    )


async def _main() -> int:
    p = argparse.ArgumentParser(description="为活动估算分项预算")
    p.add_argument("--regenerate", help="在已有预算上按指令调整,如 '整体压到 8 万以下,餐饮减 30%%'")
    args = p.parse_args()

    event = context_local.load_json("event", required=True)
    host = context_local.load_json("host", required=True)
    plan = context_local.load_json("plan") or {}

    # 命令行兜底:读 templates 同名 input(可选提供 source / ai_extracted / html_content)
    bi = context_local.load_json("budget_input") or {}
    if not plan.get("source") and bi.get("source"):
        plan["source"] = bi.get("source")
    if not plan.get("ai_extracted") and bi.get("ai_extracted"):
        plan["ai_extracted"] = bi.get("ai_extracted")
    if not plan.get("html_content") and bi.get("html_content"):
        plan["html_content"] = bi.get("html_content")
    regeneration_prompt = args.regenerate or bi.get("regeneration_prompt")

    budget = await info_budget(
        event=event, host=host, plan=plan, regeneration_prompt=regeneration_prompt,
    )

    # 语言后处理:修复结构化字段里的字面量转义
    if isinstance(budget, dict):
        for task in budget.get("task_list", []) or []:
            if isinstance(task, dict) and isinstance(task.get("task"), str):
                task["task"] = check_and_fix_escapes(task["task"])

    context_local.save_json("budget", budget)
    context_local.merge_into("plan", {"budget": budget})

    out = {
        "ok": True,
        "workdir": str(context_local.workdir()),
        "written": ["budget.json", "plan.json(merged)"],
        "regenerated": bool(regeneration_prompt),
        "notes": list(_NOTES),  # 降级/跳过备注(缺 bs4、系数降级、场地/提取失败等)
        "budget": budget,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_skill_main(_main))
