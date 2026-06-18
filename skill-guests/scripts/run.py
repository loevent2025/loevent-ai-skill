#!/usr/bin/env python3
"""
skill-guests —— 为活动嘉宾生成可信的嘉宾简介(带 grounding 校验)

对齐后端 search_guests_tools.search_guests_tool 的完整业务逻辑:
  4 维并行 Google Search(background / achievements / relevance / recent,每维都锁定身份)
  → verify_and_fix 二次 grounding 校验(CHECK / FIX 两步,内联自 company_info_tools)
  → 按"是否已有 profile"组装 synthesis prompt(无则新写、有则保留+enrichment)
  → 出结构化 {text} 简介。

只改 infra(AI 逻辑逐字搬运):
- 上下文不查 Mongo,改读本地 event.json(theme / language / time_start,由 skill-init 生成);
- 不写 DB,产物 save_json("guests") + merge 进 plan.json;
- 去掉 @track_timing 装饰器与 project 路由(engine 单 Key);user_id/event_id 用引擎默认占位;
- verify_and_fix / step1_check / step2_fix_one 内联进本脚本,保持 skill 独立可分发。

用法:
    python skill-guests/scripts/run.py                          # 读 event.json / guests_input.json
    python skill-guests/scripts/run.py --name "张三" --company "ACME" --position "CTO"
    python skill-guests/scripts/run.py --name "张三" --company "ACME" --position "CTO" \
        --profile "现有的一段嘉宾简介(有则走 enrichment,保留全部原文再增补)"

降级:任一维度搜索抛错只跳过该维(不崩);grounding/网络全失败时仍会用已得资料尽力成稿。
产物:guests.json 写入工作目录,并 merge 进 plan.json;结构化结果打印到 stdout。
agent 按 SKILL.md「结果呈现」把它整理成可读简介再给用户,不要直接甩 JSON。
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime

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
)
from engine.schemas.guests_models import GuestProfileOut  # noqa: E402

# module 名(对齐后端 search_guests_tools 的常量,仅用于日志/计费打点)
SEARCH_GUESTS = "search_guests"
GOOGLE_SEARCH_GUESTS = "google_search_guests"


# ─────────────────────────────────────────────────────────────
# 内联:verify_and_fix(从 module_tools/company_info_tools.py 搬运 CHECK / FIX 两步 grounding 校验)
#   保持 skill 自包含——CHECK_PROMPT / FIX_PROMPT 复用 engine/config/company_info.yaml。
# ─────────────────────────────────────────────────────────────
async def _step1_check(*, data, tool, context=""):
    model_prompt = load_yaml("company_info.yaml")
    prompt = safe_render(
        model_prompt["CHECK_PROMPT"],
        content=json.dumps(data, ensure_ascii=False, indent=2),
        context=context,
    )
    llm = get_llm_client()
    response = await llm.generate(module=tool, prompt=prompt, use_google_search=True)
    return response.text


async def _step2_fix_one(*, field, value, tool, context=""):
    model_prompt = load_yaml("company_info.yaml")
    prompt = safe_render(
        model_prompt["FIX_PROMPT"],
        data=field,
        issues_text=value,
        context=context,
    )
    llm = get_llm_client()
    response = await llm.generate(module=tool, prompt=prompt, use_google_search=True)
    return response.text


async def _verify_and_fix(*, data, tool, context=""):
    """二次 grounding 校验:CHECK 找出确凿错误,有错则 FIX 定点修正,否则原样返回。"""
    issues_text = await _step1_check(data=data, tool=tool, context=context)
    if issues_text.strip("`").strip() == "NO_ISSUES":
        return {"data": data, "corrected": False}
    fixed_data = await _step2_fix_one(field=data, value=issues_text, tool=tool, context=context)
    return {"data": fixed_data, "corrected": True}


# ─────────────────────────────────────────────────────────────
# 4 维并行搜索(逐字搬运,每维都锁定身份、限 2 条 query)
# ─────────────────────────────────────────────────────────────
async def _search_single_dimension(*, dimension_name, focus, guest_name, guest_company, guest_title):
    prompt = f"""
    # Search Target
    Search for "{dimension_name}" information of this guest:
    - Name: {guest_name}
    - Company: {guest_company}
    - Title: {guest_title}

    # IDENTITY VERIFICATION (CRITICAL)
    - MUST confirm information is about "{guest_name}" from "{guest_company}"
    - IGNORE information about different people with the same name

    # SEARCH QUERY LIMIT (IMPORTANT)
    - Use a MAXIMUM of 2 Google Search queries for this task
    - If 2 queries return no results, STOP and return "No relevant information found"
    - DO NOT generate additional queries beyond 2

    # Search Focus
    {focus}

    # Output Format
    - Extract ONLY "{dimension_name}" related information
    - Label source type (official bio / media / wiki)
    - Mark as "CONFIRMED" or "UNVERIFIED"
    - Return "No relevant information found" if nothing found
    """
    llm = get_llm_client()
    result = await llm.generate(module=GOOGLE_SEARCH_GUESTS, prompt=prompt, use_google_search=True)
    return {"dimension": dimension_name, "content": result.text}


async def _parallel_search(*, guest_name, guest_company, guest_title, event_topic, time_start):
    """并行执行 4 轮搜索 —— 每轮都锁定身份。"""
    # 基于 time_start 算近 6 个月范围(用于 recent 维度的时效约束)
    now = datetime.strptime(time_start[:10], "%Y-%m-%d")
    six_months_ago = now - relativedelta(months=6)
    current_date = now.strftime("%Y年%m月")        # 例:2026年09月
    start_date = six_months_ago.strftime("%Y年%m月")  # 例:2026年03月

    identity = {
        "guest_name": guest_name,
        "guest_company": guest_company,
        "guest_title": guest_title,
    }

    search_tasks = [
        _search_single_dimension(
            dimension_name="background",
            focus=f"""
            1. CONFIRM this person is {guest_title} at {guest_company}
            2. Education and career history
            3. Responsibilities at {guest_company}
            4. Distinguish "CURRENT" vs "FORMER" positions
            """,
            **identity,
        ),
        _search_single_dimension(
            dimension_name="achievements",
            focus=f"""
            1. Major achievements at {guest_company} or industry
            2. Awards, publications, key speeches
            3. Investment projects - MUST DISTINGUISH:
            - "LED": Clearly reported as lead investor
            - "PARTICIPATED": Part of investment team
            - "FIRM-LEVEL": Only firm invested, no personal role mentioned
            4. Use ONLY titles with clear sources
            """,
            **identity,
        ),
        _search_single_dimension(
            dimension_name="relevance",
            focus=f"""
            1. Experience in "{event_topic}" related fields
            2. Published viewpoints, speeches, articles
            3. When citing their concepts - MUST be COMPLETE:
            - Full concept name and meaning
            - When/where proposed
            4. Include source for all insights
            """,
            **identity,
        ),
        _search_single_dimension(
            dimension_name="recent",
            focus=f"""
            1. Updates within past 6 months ({start_date} to {current_date})
            2. New projects, speeches, viewpoints
            3. VERIFY timing - must be recent, NOT historical
            """,
            **identity,
        ),
    ]

    dimension_order = ["background", "achievements", "relevance", "recent"]
    results = await asyncio.gather(*search_tasks, return_exceptions=True)

    collected = {}
    notes = []
    for name, r in zip(dimension_order, results):
        if isinstance(r, Exception):
            # 不静默吞:把失败维度计入结构化 note,供上层透传给用户
            notes.append(f"维度 {name} 搜索失败({type(r).__name__}: {r}),已跳过该维度。")
            continue
        collected[r["dimension"]] = r["content"]
    return collected, notes


# ─────────────────────────────────────────────────────────────
# synthesis prompt 组装(逐字搬运:有 profile 走 enrichment、无则新写)
# ─────────────────────────────────────────────────────────────
def _build_synthesis_prompt(*, guest_name, guest_company, guest_title, event_topic,
                            output_language, search_results, guest_profile=None):
    output_language = (output_language or "中文").upper()
    if guest_profile:
        return f"""
            # Role
            Professional event copywriter, known for RIGOR and ACCURACY.

            # Task
            Polish and ENRICH the existing guest introduction based on search results.
            You MUST KEEP all existing content — DO NOT delete or omit any original information.
            Add new relevant details, improve fluency, and enhance the overall quality.

            # Existing Profile (MUST RETAIN ALL CONTENT)
            {guest_profile}

            # Guest Info
            - Name: {guest_name}
            - Company: {guest_company}
            - Title: {guest_title}

            # Event Topic
            {event_topic}

            # Output Language
            {output_language}
            - MUST write ENTIRELY in {output_language}

            # Search Results
            Raw search data containing background, achievements, relevance, and recent updates. Extract useful information and discard anything irrelevant or unverifiable.
            {search_results}

            # ENRICHMENT GUIDELINES
            1. **PRESERVE**: Keep ALL original content intact — treat existing text as the baseline
            2. **ENRICH**: Add new sourced information (recent updates, achievements, event relevance)
            3. **POLISH**: Improve sentence flow, transitions, and overall readability
            4. **INTEGRATE**: Seamlessly blend new information into the existing text

            # ACCURACY REQUIREMENTS (HIGHEST PRIORITY)

            ## Identity
            - CONFIRM person matches "{guest_name}" from "{guest_company}"
            - REMOVE any same-name mix-ups from search results (NOT from existing profile)

            ## Investment Role Wording
            | Evidence | Correct | Wrong |
            |----------|---------|-------|
            | Led/led round | "Led investment in XX" | - |
            | Participated | "Participated in XX" | "Led investment" |
            | Firm only | "Firm invested in XX" | "They invested" |
            | No evidence | DO NOT MENTION | Any claim |

            ## Concepts/Viewpoints
            - MUST include COMPLETE meaning when citing
            - If unsure, use "proposed XX concept" WITHOUT elaboration

            ## Titles
            - ✅ Sourced titles only
            - ❌ NO fabricated evaluations
            - ❌ NO unsourced modifiers

            ## FORBIDDEN
            - ❌ Deleting or omitting ANY existing profile content
            - ❌ Fabricating unsourced information
            - ❌ Speculating viewpoints/achievements
            - ❌ Vague hedging ("reportedly", "possibly")
            - ❌ Mixing different people's information
            - ❌ Exaggerating roles

            # Output Format
            - Fluent paragraphs, NO bullets or subheadings
            - Chinese ≤200 chars / English ≤200 words (slightly longer to accommodate enrichment)
            - MUST output in {output_language} regardless of source language
            - Pure copy only, NO prefixes or explanations
            - WHEN IN DOUBT about NEW info, OMIT — BETTER MISSING THAN WRONG
            - But NEVER omit EXISTING profile content
            """
    return f"""
            # Role
            Professional event copywriter, known for RIGOR and ACCURACY.

            # Task
            Write guest introduction based on search results.

            # Guest Info
            - Name: {guest_name}
            - Company: {guest_company}
            - Title: {guest_title}

            # Event Topic
            {event_topic}

            # Output Language
            {output_language}
            - MUST write ENTIRELY in {output_language}

            # Search Results
            Raw search data containing background, achievements, relevance, and recent updates. Extract useful information and discard anything irrelevant or unverifiable.
            {search_results}

            # Output Structure
            1. **Opening (60%)**: Recent updates + relevance to event topic
            2. **Closing (40%)**: Career background + 1-2 key achievements

            # ACCURACY REQUIREMENTS (HIGHEST PRIORITY)

            ## Identity
            - CONFIRM person matches "{guest_name}" from "{guest_company}"
            - REMOVE any same-name mix-ups

            ## Investment Role Wording
            | Evidence | Correct | Wrong |
            |----------|---------|-------|
            | Led/led round | "Led investment in XX" | - |
            | Participated | "Participated in XX" | "Led investment" |
            | Firm only | "Firm invested in XX" | "They invested" |
            | No evidence | DO NOT MENTION | Any claim |

            ## Concepts/Viewpoints
            - MUST include COMPLETE meaning when citing
            - If unsure, use "proposed XX concept" WITHOUT elaboration

            ## Titles
            - ✅ Sourced titles only
            - ❌ NO fabricated evaluations
            - ❌ NO unsourced modifiers

            ## FORBIDDEN
            - ❌ Fabricating unsourced information
            - ❌ Speculating viewpoints/achievements
            - ❌ Vague hedging ("reportedly", "possibly")
            - ❌ Mixing different people's information
            - ❌ Exaggerating roles

            # Output Format
            - Fluent paragraphs, NO bullets or subheadings
            - Chinese ≤150 chars / English ≤150 words
            - MUST output in {output_language} regardless of source language
            - Pure copy only, NO prefixes or explanations
            - WHEN IN DOUBT, OMIT — BETTER MISSING THAN WRONG
            """


async def search_guest(*, event, guest_name, guest_company, guest_position, guest_profile=None):
    """嘉宾搜索主流程,context 改为 event.json 注入(不查 DB)。

    返回 (profile_text, notes):notes 收集搜索/校验降级的结构化说明,供上层透传。
    """
    output_language = event.get("language")
    guest_title = guest_position
    event_topic = event.get("theme")
    time_start = event.get("time_start")

    notes = []

    # 1) 4 维并行 grounding 搜索(失败维度计入 notes,不静默丢)
    search_results, search_notes = await _parallel_search(
        guest_name=guest_name,
        guest_company=guest_company,
        guest_title=guest_title,
        event_topic=event_topic,
        time_start=time_start,
    )
    notes.extend(search_notes)

    # 2) 二次验证:检查搜索结果准确性并修正(grounding 失败时降级:沿用原始搜索结果,并记 note)
    try:
        verified = await _verify_and_fix(
            data=search_results,
            tool=SEARCH_GUESTS,
            context=f"{guest_name}, {guest_company}, {guest_title}",
        )
        search_results = verified["data"]
    except Exception as e:
        notes.append(f"二次 grounding 校验降级({type(e).__name__}: {e}),沿用原始搜索结果。")

    # 3) 组 prompt → 出结构化 {text}
    synthesis_prompt = _build_synthesis_prompt(
        guest_name=guest_name,
        guest_company=guest_company,
        guest_title=guest_title,
        event_topic=event_topic,
        output_language=output_language,
        search_results=search_results,
        guest_profile=guest_profile,
    )

    llm = get_llm_client()
    profile_resp = await llm.generate(
        module=SEARCH_GUESTS,
        prompt=synthesis_prompt,
        response_schema=GuestProfileOut,
    )
    data = parse_structured(profile_resp, GuestProfileOut)
    return data.text, notes


def _resolve_inputs(args) -> dict:
    """优先读 guests_input.json,CLI 参数覆盖;name/company/position 为必填。"""
    data = context_local.load_json("guests_input") or {}
    return {
        "guest_name": args.name or data.get("guest_name"),
        "guest_company": args.company or data.get("guest_company"),
        "guest_position": args.position or data.get("guest_position"),
        "guest_profile": args.profile or data.get("guest_profile"),
    }


async def _main() -> int:
    p = argparse.ArgumentParser(description="为活动嘉宾生成可信的嘉宾简介(带 grounding 校验)")
    p.add_argument("--name", help="嘉宾姓名(必填)")
    p.add_argument("--company", help="嘉宾所属公司/机构(必填)")
    p.add_argument("--position", help="嘉宾职位/头衔(必填)")
    p.add_argument("--profile", help="已有嘉宾简介(可选;有则走 enrichment,保留原文再增补)")
    args = p.parse_args()

    event = context_local.load_json("event", required=True)
    inp = _resolve_inputs(args)

    missing = [k for k in ("guest_name", "guest_company", "guest_position") if not inp.get(k)]
    if missing:
        print(json.dumps({
            "ok": False,
            "error": f"缺少必填字段:{', '.join(missing)}。"
                     f"请用 --name/--company/--position 传入,或写进工作目录的 guests_input.json。",
        }, ensure_ascii=False, indent=2))
        return 2

    profile, notes = await search_guest(event=event, **inp)

    if not profile:
        print(json.dumps({
            "ok": False,
            "guest_name": inp["guest_name"],
            "error": "未能生成嘉宾简介(可能是搜索全失败 / Key 无 grounding 权限 / 网络问题)。"
                     "先跑 python engine/doctor.py 探一下权限,或稍后重试。",
        }, ensure_ascii=False, indent=2))
        return 1

    result = {
        "ok": True,
        "workdir": str(context_local.workdir()),
        "guest_name": inp["guest_name"],
        "guest_company": inp["guest_company"],
        "guest_position": inp["guest_position"],
        "enriched": bool(inp.get("guest_profile")),
        "profile": profile,
    }
    if notes:
        result["notes"] = notes

    # 多嘉宾累加:guests.json 存 {嘉宾名: 简介} 字典
    existing = context_local.load_json("guests") or {}
    if not isinstance(existing, dict) or "guests" not in existing:
        existing = {"guests": {}}
    existing["guests"][inp["guest_name"]] = {
        "company": inp["guest_company"],
        "position": inp["guest_position"],
        "profile": profile,
    }
    context_local.save_json("guests", existing)
    context_local.merge_into("plan", {"guests": existing["guests"]})

    result["written"] = ["guests.json", "plan.json(merged)"]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_skill_main(_main))
