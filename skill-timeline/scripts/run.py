#!/usr/bin/env python3
"""
skill-timeline —— 为活动生成/优化筹备时间线(任务 + 起止日期 + 优先级)

对齐后端 timeline_model.timeline,但:
- 上下文不查 Mongo:event 基础信息读 event.json、主办方读 host.json;
  「场景定位/目标/嘉宾/流程」这类业务字段读 plan.json(双源,见下)。
- 任何 DB 写 → save_json("timeline") + merge_into("plan", {"timeline": ...})。
- 去掉 @track_timing、project 路由;engine 单 Key,user_id/event_id 用占位。

双源上下文(忠实搬后端 source 判断)
----------------------------------
后端按 generated_fullplan.source 决定从哪取业务字段:
  - source == "ai_extracted" → 取 ai_extracted.{scene_type,event_scale,goal,content,guests}
  - 其它(ai_generated 等)     → 取 eventplanner_key 的扁平字段
                                 (eventGoal/eventTone/eventType/organizerProfile/guestInfo/eventFlow…)
单机版把这两套都收进 plan.json:
  - 若 plan.json 里有 "ai_extracted" 字典 → 走 ai_extracted 路径;
  - 否则把 plan.json 当成扁平 eventplanner 字段集 → 走 generated 路径。

日期数学(EVENT_SCALE_CONFIG + calculate_actual_duration)逐字搬运,
对 timeline_tool 知识库里每个任务的 duration_days 做类别缩放。

用法:
    python skill-timeline/scripts/run.py
    python skill-timeline/scripts/run.py --start 2026-01-21 --prompt "嘉宾以 VC 为主,提前锁场地"

产物:timeline.json 写入工作目录,并 merge 进 plan.json;结构化结果打到 stdout。
结果由 Claude 按 SKILL.md「结果呈现」整理后给用户,不要直接甩 JSON。
"""

import argparse
import json
import math
import os
import sys
from datetime import date, datetime

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
from engine.model_config import industry_map  # noqa: E402
from engine.schemas.timeline_models import TimelineOutput  # noqa: E402

# ── 常量(内联自后端 constants.py,保持 skill 自包含)────────────
SOURCE_AI_EXTRACTED = "ai_extracted"
GUEST_STATUS_CONFIRMED = "confirmed"
GUEST_STATUS_RECOMMENDED = "recommended"

# ── 规模 → 基准筹备天数(逐字搬自 timeline_model.EVENT_SCALE_CONFIG)──
EVENT_SCALE_CONFIG = {
    "small": 35,    # 基准时长 5周
    "medium": 120,  # 基准时长 4个月
    "large": 240,   # 基准时长 8个月
}

# 筹备开始日的兜底默认 = 运行时「今天」(用户没选/没填时用);绝不写死日期(会过期成过去日把排期算坏)。
# 注:正路是 SKILL.md 让 agent 用 AskUserQuestion 让用户选/填,这里只是漏问时的安全兜底。
DEFAULT_START_DATE = date.today().isoformat()
TIMELINE_MODULE = "timeline_tool"  # 后端 tool=模块名;engine 单 Key,仅用于日志/标识


def _validate_ymd(label: str, value) -> None:
    """校验日期为 YYYY-MM-DD;非法/缺失抛带字段名的清晰 ValueError(交调用方转 note)。"""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} 为空或非字符串(需 YYYY-MM-DD),实际:{value!r}")
    try:
        datetime.strptime(value.strip()[:10], "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"{label} 不是合法的 YYYY-MM-DD 日期:{value!r}({e})") from e


# ── 日期缩放(逐字搬自后端 calculate_actual_duration)──────────────
def calculate_actual_duration(baseline_duration: int, start_date: str, end_date: str) -> dict:
    """根据筹备期与基准时长计算各类别时间缩放系数。"""
    start_date = start_date.strip()[:10]
    start_date = datetime.strptime(start_date, "%Y-%m-%d")

    end_date = end_date.strip()[:10]
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    prep_days = (end_date - start_date).days

    if prep_days <= 0:
        raise ValueError("结束日期(活动日期)必须晚于开始日期(筹备开始日)")

    mc_scale_factor = (prep_days / baseline_duration) ** 0.7
    gv_scale_factor = math.sqrt(prep_days / baseline_duration)

    return {
        "General": gv_scale_factor,
        "Commercial": mc_scale_factor,
        "Venue": gv_scale_factor,
        "Marketing": mc_scale_factor,
    }


# ── 双源业务字段抽取(对齐后端 source 分支)─────────────────────
def _build_prompt_vars(plan: dict, host: dict) -> tuple:
    """从 plan(双源)+ host 组装 prompt 变量,返回 (prompt_vars, scene_type, event_scale)。"""
    ai_extracted = plan.get("ai_extracted")

    if isinstance(ai_extracted, dict) and ai_extracted:
        # —— ai_extracted 路径 ——
        # init 把 scene_type/event_scale 写在 plan 顶层(不在 ai_extracted 里),故顶层优先,ai_extracted 兜底
        scene_type = (plan.get("scene_type") or ai_extracted.get("scene_type") or "business_conferences").lower()
        event_scale = plan.get("event_scale") or ai_extracted.get("event_scale") or "medium"

        # 嘉宾数组转文本(confirmed 优先,其次 recommended)
        guests_raw = ai_extracted.get("guests") or {}
        if isinstance(guests_raw, dict):
            guests_list = (
                guests_raw.get(GUEST_STATUS_CONFIRMED)
                or guests_raw.get(GUEST_STATUS_RECOMMENDED)
                or []
            )
        else:
            guests_list = guests_raw
        if isinstance(guests_list, list):
            guest_info = "; ".join(
                f"{g.get('text', '')} — {g.get('detail', '')}" for g in guests_list
            )
        else:
            guest_info = str(guests_list)

        prompt_vars = {
            "event_type": "",
            "scene_type": scene_type,
            "event_scale": event_scale,
            "event_tone": "",
            "organizer_profile": host.get("host_profile") or "",
            "guest_info": guest_info,
            "event_goal": ai_extracted.get("goal", ""),
            "short_term_goals": "",
            "mid_term_goals": "",
            "long_term_goals": "",
            "twitter_metrics": "",
            "event_flow": ai_extracted.get("content", ""),
        }
    else:
        # —— generated / 扁平 eventplanner 路径 ——
        scene_type = plan.get("scene_type", "business_conferences").lower()
        event_scale = plan.get("event_scale", "medium")

        prompt_vars = {
            "event_type": plan.get("eventType", ""),
            "scene_type": scene_type,
            "event_scale": event_scale,
            "event_tone": plan.get("eventTone", ""),
            "organizer_profile": plan.get("organizerProfile", "") or host.get("host_profile", ""),
            "guest_info": plan.get("guestInfo", ""),
            "event_goal": plan.get("eventGoal", ""),
            "short_term_goals": plan.get("shortTermGoals", ""),
            "mid_term_goals": plan.get("midTermGoals", ""),
            "long_term_goals": plan.get("longTermGoals", ""),
            "twitter_metrics": plan.get("twitterMetrics", ""),
            "event_flow": plan.get("eventFlow", ""),
        }

    return prompt_vars, scene_type, event_scale


def _load_scene_tasks(scene_type: str, industry: str, event_scale: str) -> list:
    """读 timeline_tool 知识库 json(路径改用 config_path,随 bundle 走),按行业+规模取任务。

    缺文件/缺行业/缺规模时给清晰报错(知识库不全属于硬错误,无法生成基线任务)。
    """
    p = config_path("timeline_tool", f"{scene_type}.json")
    if not p.exists():
        avail = sorted(x.stem for x in config_path("timeline_tool").glob("*.json"))
        raise FileNotFoundError(
            f"找不到场景知识库 {p.name}(场景 scene_type={scene_type})。"
            f"可用场景:{', '.join(avail)}。请在 plan.json/ai_extracted 里把 scene_type 设为其中之一。"
        )

    timeline_tasks = json.loads(p.read_text(encoding="utf-8"))

    by_industry = timeline_tasks.get(industry)
    if not isinstance(by_industry, dict):
        raise KeyError(
            f"场景 {scene_type} 的知识库里没有行业 '{industry}'(可用:{list(timeline_tasks.keys())})。"
            f"检查 host.json 的 industry,或它经 industry_map 映射后的结果。"
        )

    tasks = by_industry.get(event_scale)
    if not isinstance(tasks, list):
        raise KeyError(
            f"场景 {scene_type}/行业 {industry} 下没有规模 '{event_scale}'(可用:{list(by_industry.keys())})。"
        )
    return tasks


async def build_timeline(*, event: dict, host: dict, plan: dict,
                         start_date: str, user_tasks: list, prompt: str) -> dict:
    """对齐后端 timeline():取双源业务字段 → 读知识库 → 缩放 duration → LLM 优化时间线。"""
    prompt_vars, scene_type, event_scale = _build_prompt_vars(plan, host)

    # 行业映射(与后端一致:host.industry 经 industry_map)
    industry = industry_map.get(host.get("industry"))
    if industry is None:
        # industry_map 未命中时,后端会拿 None 去 .get(None) 取不到任务;这里给明确提示
        raise KeyError(
            f"host.json 的 industry='{host.get('industry')}' 不在 industry_map 内,"
            f"无法定位知识库行业。支持值见 engine/model_config.industry_map。"
        )

    tasks = _load_scene_tasks(scene_type, industry, event_scale)

    # 日期格式校验:非法不直接崩(deep strptime traceback),给清晰提示。
    event_date = event.get("time_start")
    try:
        _validate_ymd("筹备开始日 start_date", start_date)
        _validate_ymd("活动日期 event.time_start", event_date)
    except ValueError as e:
        raise ValueError(
            f"无法计算时间线:{e}。请把日期改成 YYYY-MM-DD 格式"
            f"(start_date 用 --start 或 timeline_input.json,活动日期改 event.json 的 time_start)。"
        ) from e

    # 类别缩放系数(基准天数来自 EVENT_SCALE_CONFIG)。
    # prep_days<=0(活动日期不晚于筹备开始日)在此兜住,转清晰提示而非裸 ValueError。
    try:
        multipliers = calculate_actual_duration(
            baseline_duration=EVENT_SCALE_CONFIG.get(event_scale, EVENT_SCALE_CONFIG["medium"]),
            end_date=event_date,
            start_date=start_date,
        )
    except ValueError as e:
        raise ValueError(
            f"无法计算时间线:{e}(start_date={start_date} / event.time_start={event_date})。"
            f"请确保活动日期晚于筹备开始日。"
        ) from e

    # 就地把每个任务的 duration_days 按其 category 缩放(逐字搬后端 for 循环)
    for task in tasks:
        category = task.get("category")
        multiplier = multipliers.get(category, 1.0)
        task["duration_days"] = round(task["duration_days"] * multiplier)

    system_prompt_data = load_yaml("timeline.yaml")
    language = event.get("language", "中文")

    user_prompt = safe_render(
        system_prompt_data["timeline_user_prompt"],
        # 基础信息
        event_name=event.get("event_name"),
        theme=event.get("theme"),
        start_date=start_date,
        event_date=event.get("time_start"),
        language=language,
        prompt=prompt,
        # 任务数据
        tasks=tasks,
        task_count=len(tasks) if isinstance(tasks, list) else 0,
        user_tasks=user_tasks,
        # 双源业务字段
        **prompt_vars,
    )
    system_prompt = system_prompt_data["timeline_system_prompt"]

    llm = get_llm_client()
    resp = await llm.generate(
        module=TIMELINE_MODULE,
        prompt=user_prompt,
        system_prompt=system_prompt,
        response_schema=TimelineOutput,
    )
    data = parse_structured(resp, TimelineOutput).model_dump()
    return {
        "data": data,
        "meta": {
            "scene_type": scene_type,
            "event_scale": event_scale,
            "industry": industry,
            "start_date": start_date,
            "event_date": event.get("time_start"),
            "baseline_tasks": len(tasks) if isinstance(tasks, list) else 0,
            "multipliers": {k: round(v, 4) for k, v in multipliers.items()},
        },
    }


def _resolve_inputs(args) -> dict:
    """优先读 timeline_input.json,CLI 覆盖;给合理缺省。"""
    data = context_local.load_json("timeline_input") or {}
    return {
        "start_date": args.start or data.get("preparation_start_date"),
        "user_tasks": data.get("user_tasks", []),
        "prompt": args.prompt or data.get("prompt", ""),
    }


async def _main() -> int:
    p = argparse.ArgumentParser(description="为活动生成/优化筹备时间线")
    p.add_argument("--start", help=f"筹备开始日 YYYY-MM-DD(默认 {DEFAULT_START_DATE})")
    p.add_argument("--prompt", help="额外的筹备说明(如嘉宾构成、硬约束)")
    args = p.parse_args()

    event = context_local.load_json("event", required=True)
    host = context_local.load_json("host", required=True)
    # plan 是各 skill 的产物累加器;timeline 依赖里面的业务字段(双源)。
    # 缺 plan 不致命:走全缺省(scene_type=business_conferences / scale=medium),仍能出基线时间线。
    plan = context_local.load_json("plan") or {}
    inputs = _resolve_inputs(args)
    if not inputs["start_date"]:
        print(json.dumps({
            "ok": False,
            "error": f"缺少必填字段:筹备开始日 preparation_start_date(无安全默认,写死会过期)。"
                     f"请用 --start YYYY-MM-DD 传入,或写进 timeline_input.json;"
                     f"建议先用 AskUserQuestion 问用户筹备何时启动(可建议默认今天 {DEFAULT_START_DATE})。",
        }, ensure_ascii=False, indent=2))
        return 2

    result = await build_timeline(event=event, host=host, plan=plan, **inputs)

    timeline_doc = {
        "ok": True,
        "workdir": str(context_local.workdir()),
        **result["meta"],
        "tasks": result["data"].get("tasks", []),
    }
    context_local.save_json("timeline", timeline_doc)
    context_local.merge_into("plan", {"timeline": timeline_doc})

    out = {
        "ok": True,
        "workdir": str(context_local.workdir()),
        "written": ["timeline.json", "plan.json(merged)"],
        "timeline": timeline_doc,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_skill_main(_main))
