#!/usr/bin/env python3
"""
skill-audience —— 为活动推断目标受众画像(主/次/延伸人群 + 痛点)

对齐后端 target_audience_generator.infer_audience,但:
- 上下文不查 Mongo,改读本地 event.json / host.json(由 skill-init 生成);
- event_goal / prompt_objective / GTMmatrix 由用户提供(读 audience_input.json 或 CLI)。

用法:
    python run.py                       # 读工作目录的 event.json/host.json/audience_input.json
    python run.py --goal product --objective "拉新开发者" \
        --growth-label 获取 --growth-value 40 --lifecycle-label 早期 --lifecycle-value 30

产物:audience.json 写入工作目录,并 merge 进 plan.json;结构化结果打印到 stdout。
agent 按 SKILL.md「结果呈现」把它整理成可读格式再给用户,不要直接甩 JSON。
"""

import argparse
import json
import logging
import os
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
from engine.model_config import industry_map  # noqa: E402
from engine.schemas.audience_models import AudienceOutput  # noqa: E402

logger = logging.getLogger("loevent.audience")


async def infer_audience(*, event: dict, host: dict, event_goal: str,
                         prompt_objective: str, GTMmatrix: dict) -> dict:
    """对齐后端 infer_audience,context 改为入参注入(不查 DB)。"""
    target_audience = load_yaml("target_audience.yaml")
    industry = industry_map.get(host.get("industry"))

    audience_system_prompt = target_audience.get("target_audience_system")
    audience_user_prompt = safe_render(
        target_audience.get("target_audience_user"),
        theme=event.get("theme"),
        attendees=event.get("attendees"),
        language=event.get("language"),
        event_name=event.get("event_name"),
        organization_name=host.get("host_name"),
        industry=host.get("industry"),
        host_profile=host.get("host_profile"),
        event_goal=event_goal,
        prompt_objective=prompt_objective,
        growth_mode_direction=GTMmatrix.get("growth_mode", {}).get("label"),
        growth_mode_value=GTMmatrix.get("growth_mode", {}).get("value"),
        lifecycle_direction=GTMmatrix.get("lifecycle", {}).get("label"),
        lifecycle_value=GTMmatrix.get("lifecycle", {}).get("value"),
        industry_knowledge=target_audience.get(f"target_audience_{industry}"),
    )
    llm = get_llm_client()
    resp = await llm.generate(
        module="info_audience",
        prompt=audience_user_prompt,
        system_prompt=audience_system_prompt,
        response_schema=AudienceOutput,
    )
    return parse_structured(resp, AudienceOutput).model_dump()


def _axis(raw: dict, key: str, default_label: str, default_value: int) -> dict:
    """从 GTMmatrix 取一根轴(growth_mode / lifecycle),缺键/非 dict/缺字段都给缺省。

    防 audience_input.json 里 GTMmatrix 只填了一半(如只有 growth_mode、或 value 漏了)
    导致后续 gtm[key]["label"] KeyError。
    """
    node = raw.get(key)
    if not isinstance(node, dict):
        node = {}
    label = node.get("label")
    value = node.get("value")
    return {
        "label": label if label is not None else default_label,
        "value": value if value is not None else default_value,
    }


def _resolve_inputs(args, plan: dict = None) -> dict:
    """GTM 读取链:CLI > audience_input.json > plan.gtm > 默认。其余优先读 audience_input.json,CLI 覆盖。"""
    data = context_local.load_json("audience_input")
    if data is None:
        logger.info(
            "未找到 audience_input.json(在 %s),使用 CLI 参数 / plan.gtm / 缺省值推断受众。",
            context_local.workdir(),
        )
        data = {}

    # 前置 2×2 GTM 象限:audience_input 没填就回落到 plan.gtm(用户前置选过的单一真源)
    raw_gtm = data.get("GTMmatrix") or (plan or {}).get("gtm")
    if not isinstance(raw_gtm, dict):
        raw_gtm = {}

    gtm = {
        "growth_mode": _axis(
            raw_gtm, "growth_mode",
            data.get("growth_label", "获取"), data.get("growth_value", 30),
        ),
        "lifecycle": _axis(
            raw_gtm, "lifecycle",
            data.get("lifecycle_label", "早期"), data.get("lifecycle_value", 30),
        ),
    }
    if args.growth_label or args.growth_value is not None:
        gtm["growth_mode"] = {"label": args.growth_label or gtm["growth_mode"]["label"],
                              "value": args.growth_value if args.growth_value is not None else gtm["growth_mode"]["value"]}
    if args.lifecycle_label or args.lifecycle_value is not None:
        gtm["lifecycle"] = {"label": args.lifecycle_label or gtm["lifecycle"]["label"],
                            "value": args.lifecycle_value if args.lifecycle_value is not None else gtm["lifecycle"]["value"]}
    return {
        "event_goal": args.goal or data.get("event_goal", "product"),
        "prompt_objective": args.objective or data.get("prompt_objective", ""),
        "GTMmatrix": gtm,
    }


async def _main() -> int:
    p = argparse.ArgumentParser(description="为活动推断目标受众画像")
    p.add_argument("--goal", help='event_goal: product | ecosystem | brand')
    p.add_argument("--objective", help="一句话目标描述")
    p.add_argument("--growth-label", dest="growth_label")
    p.add_argument("--growth-value", dest="growth_value", type=int)
    p.add_argument("--lifecycle-label", dest="lifecycle_label")
    p.add_argument("--lifecycle-value", dest="lifecycle_value", type=int)
    args = p.parse_args()

    event = context_local.load_json("event", required=True)
    host = context_local.load_json("host", required=True)
    plan = context_local.load_json("plan") or {}
    inputs = _resolve_inputs(args, plan)

    audience = await infer_audience(event=event, host=host, **inputs)

    context_local.save_json("audience", audience)
    # 受众 + 前置采集的 GTM 象限一起写回 plan(plan.gtm 是单一真源,供 eventplanner 复用)
    context_local.merge_into("plan", {"audience": audience, "gtm": inputs["GTMmatrix"]})

    out = {"ok": True, "workdir": str(context_local.workdir()),
           "written": ["audience.json", "plan.json(merged)"], "audience": audience}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_skill_main(_main))
