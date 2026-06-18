#!/usr/bin/env python3
"""
skill-init —— 把一段活动描述,抽成本地的 event.json / host.json / plan.json

它是整个 bundle 的「入口」:其它 skill(受众/预算/时间线…)都从这三个文件读上下文。
对应后端 eventplanner_extractor.extract_from_raw_text + extract_plan_service 的映射,
但去掉 DB 落库与 Google Maps 地理编码(单机版不需要)。

用法:
    python init_event.py path/to/活动描述.txt
    python init_event.py --text "一段活动描述…"
    echo "活动描述" | python init_event.py        # 从 stdin 读

产物写入工作目录(默认当前目录,可用 LOEVENT_WORKDIR 指定):
    event.json / host.json / plan.json
并把结构化结果打印到 stdout(JSON),供 agent 整理后呈现给用户。
"""

import argparse
import json
import os
import sys
from datetime import datetime

# 让脚本能 import engine(bundle 根目录加入 path)
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
from engine.schemas.init_models import ExtractResult  # noqa: E402

# AI schema industry → 前端/DB industry(对齐后端 extract_plan_service.INDUSTRY_MAP)
INDUSTRY_MAP = {"technology": "AI & Technology", "web3": "WEB 3", "other": "General"}

# 收集非致命警告(语言值映射等),计入结构化返回的 notes,而非吞掉。
_NOTES: list = []


async def extract_from_raw_text(raw_text: str) -> dict:
    """对齐后端 eventplanner_extractor.extract_from_raw_text(去 track_timing 装饰)。"""
    prompt_data = load_yaml("eventplanner_extractor.yaml")
    system_prompt = prompt_data["system_prompt"]
    user_prompt = safe_render(
        prompt_data["user_prompt"],
        raw_text=raw_text,
        current_year=datetime.now().year,
    )
    llm = get_llm_client()
    resp = await llm.generate(
        module="eventplanner_extractor",
        prompt=user_prompt,
        system_prompt=system_prompt,
        response_schema=ExtractResult,  # genai 原生吃 Pydantic BaseModel
        history=[],  # 与后端一致:走 chat API 路径
    )
    # 健壮解析:剥围栏 / 容截断 + Pydantic 校验,再转 dict 供 _to_local_files 映射
    return parse_structured(resp, ExtractResult).model_dump()


def _map_language(lang_raw: str) -> str:
    """活动语言值 → 显示语言;非预期值默认中文并记一条 warning(不静默吞掉)。

    schema enum 为 chinese/english,但模型偶发返回其它写法。预期取值之外的一律
    回落到「中文」,并把 warning 计入结构化返回的 notes,便于上层察觉降级。
    """
    v = (lang_raw or "").strip().lower()
    if v in ("english", "en"):
        return "English"
    if v in ("chinese", "zh", "中文", ""):
        return "中文"
    _NOTES.append(f"language 值非预期({lang_raw!r}),已默认中文。")
    return "中文"


def _to_local_files(result: dict) -> dict:
    """把抽取结果映射成 event/host/plan 三个本地文件(对齐 extract_plan_service,去 DB/geocode)。"""
    host = result.get("host", {}) or {}
    basic = result.get("basic", {}) or {}
    analysis = result.get("analysis", {}) or {}

    raw_industry = (host.get("industry", "") or "").strip()
    lang_raw = (basic.get("language", "chinese") or "chinese")
    display_lang = _map_language(lang_raw)
    try:
        attendees = int(basic.get("attendees", 0) or 0)
    except (ValueError, TypeError):
        attendees = 0

    host_json = {
        "host_name": (host.get("name", "") or "").strip(),
        "industry": INDUSTRY_MAP.get(raw_industry.lower(), raw_industry),
        "website": host.get("website", ""),
        "host_profile": host.get("profile", ""),
        "source": "ai_extracted",
    }
    event_json = {
        "event_name": basic.get("title", "未命名活动"),
        "theme": basic.get("theme", basic.get("title", "未命名活动")),
        "time_start": basic.get("startTime", ""),
        "time_end": basic.get("endTime", ""),
        "timezone": basic.get("timezone", "Asia/Shanghai"),
        "location": basic.get("location", ""),
        "attendees": attendees,
        "language": display_lang,
        "source": "ai_extracted",
    }
    plan_json = {
        "scene_type": result.get("scene_type", ""),
        "event_scale": result.get("event_scale", ""),
        "activate_type": result.get("activate_type", ""),
        "confirmed_audience": result.get("confirmed_audience", ""),
        "ai_extracted": {
            "goal": analysis.get("goal", ""),
            "content": analysis.get("content", ""),
            "partners": analysis.get("partners", ""),
            "marketing": analysis.get("marketing", ""),
            "venues": result.get("venues", []),
            "guests": result.get("guests", []),
            "timeline": result.get("timeline", ""),
        },
    }

    context_local.save_json("event", event_json)
    context_local.save_json("host", host_json)
    context_local.save_json("plan", plan_json)
    return {"event": event_json, "host": host_json, "plan": plan_json}


def _read_raw_text(args) -> str:
    if args.text:
        return args.text
    if args.path:
        with open(args.path, "r", encoding="utf-8") as f:
            return f.read()
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("请提供活动描述:位置参数文件路径、--text，或从 stdin 管道输入。")


async def _main() -> int:
    parser = argparse.ArgumentParser(description="把活动描述抽成本地 event/host/plan.json")
    parser.add_argument("path", nargs="?", help="活动描述文本文件路径")
    parser.add_argument("--text", help="直接传入活动描述文本")
    args = parser.parse_args()

    raw_text = _read_raw_text(args).strip()
    if not raw_text:
        raise SystemExit("活动描述为空。")

    result = await extract_from_raw_text(raw_text)
    files = _to_local_files(result)

    out = {
        "ok": True,
        "workdir": str(context_local.workdir()),
        "written": ["event.json", "host.json", "plan.json"],
        **files,
    }
    if _NOTES:
        out["notes"] = list(_NOTES)
    # 结构化结果给 agent;agent 按 SKILL.md 整理成可读格式再呈现给用户
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_skill_main(_main))
