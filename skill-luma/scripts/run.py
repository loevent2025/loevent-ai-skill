#!/usr/bin/env python3
"""
skill-luma —— 生成 Luma 活动文案(短文案 + 长文案 + 标题)

对齐后端 luma_event_tools.luma_event_description_tool +
module_tools/luma_event_description.generate_content,但:
- 上下文不查 Mongo(user_events/host_profiles/generated_fullplan),
  改读本地 event.json / host.json / plan.json(由 skill-init 生成);
- 去掉 @track_timing 装饰、去掉 project 路由(engine 单 key),user_id/event_id 不传;
- 无 DB 写,结果 save_json("luma") 并 merge 进 plan.json。

业务逻辑(忠实搬运):
- 短文案:event_description.yaml[short_copywrite] + social_poster_rc_schema → 直接出 text。
- 长文案两步:
    1) extract_with_gemini:从原始素材(raw_text / html_content)抽结构化字段(long_content schema);
    2) event_description.yaml[long_copywrite] + social_poster_rc_schema → 出 text;标题取自第一步的 luma_event_title。
- 长文案的原始素材来自 plan:source=="ai_extracted" 用 plan.ai_extracted.raw_text,否则用 plan.html_content;
  也可由用户在 description_input.json / --raw-text 显式提供。缺素材 → 只出短文案(降级,不崩)。
- 短/长并行执行(asyncio.gather, return_exceptions=True),任一失败不影响另一条。

用法:
    python skill-luma/scripts/run.py                      # 读 event.json/host.json/plan.json/description_input.json
    python skill-luma/scripts/run.py --language English
    python skill-luma/scripts/run.py --raw-text-file ./agenda.txt   # 显式提供长文案素材

产物:luma.json 写入工作目录,并 merge 进 plan.json;结构化结果打印到 stdout。
agent 按 SKILL.md「结果呈现」把它整理成可读格式再给用户,不要直接甩 JSON。
"""

import argparse
import asyncio
import json
import os
import sys

_BUNDLE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.insert(0, _BUNDLE_ROOT)

from engine import (  # noqa: E402
    get_llm_client, load_yaml, safe_render, context_local,
    parse_structured, run_skill_main,
)
from engine.schemas.luma_models import SocialPosterRcOut, LongContent  # noqa: E402

SOURCE_AI_EXTRACTED = "ai_extracted"

# 长文案抽取规则(对齐后端 extraction_prompt,逐字)。
_EXTRACTION_PROMPT = """
    请提取以下关键信息：
    - eventType: 活动类型（如 Workshop / Summit / Meetup / Hackathon 等）
    - eventFormat: 活动形式（如 Hands-on / Keynote / Panel / Structured Networking 等）
    - coreProblem: 活动解决的核心痛点或关键机会
    - keyBenefits: 参与者可获得的 4–5 个具体收益（数组形式）
    - agenda: 活动议程数组，每项需包含：
        - time: 时间段（如 “9:00 AM – 10:00 AM”）
        - activity: 活动内容（如 “Registration & Coffee”）
    - speakers: 嘉宾整体描述（含姓名、公司、职位、成就数据等）
    - luma_event_title: 获取核心命题部分的内容，不超过140个字符，如果超过进行总结提取
    """


# ── LLM 调用封装(对齐后端 generate_activity,去 user/event id 与 track_timing)──────
# 返回原始 LLMResponse,交给 parse_structured 做健壮解析(容错截断/围栏)。
async def _generate_activity(prompt: str, module: str, schema=SocialPosterRcOut):
    llm = get_llm_client()
    return await llm.generate(module=module, prompt=prompt, response_schema=schema)


# ── 短文案(对齐 _generate_short_content)──────────────────────────────────────────
async def _generate_short_content(*, gen_prompt, event, host, language, module) -> str:
    prompt = safe_render(
        gen_prompt["short_copywrite"],
        theme=event.get("theme"),
        startDate=event.get("time_start"),
        endDate=event.get("time_end"),
        preparationStartDate=event.get("created_at"),
        location=event.get("location"),
        attendees=event.get("attendees"),
        organization=host.get("host_name"),
        language=language,
    )
    resp = await _generate_activity(prompt, module)
    return parse_structured(resp, SocialPosterRcOut).text


# ── 长文案第一步:抽取结构化字段(对齐 extract_with_gemini)────────────────────────
async def _extract_with_gemini(raw_output: str, module: str) -> dict:
    messages = f"""# Task
        Extract key information from the following text and return in JSON format.
        # Requirements
        1. Only output valid JSON, without any explanations, comments, or markdown code block markers
        2. Ensure information is accurate and complete, use null for missing fields
        3. Preserve the original semantics, do not speculate or fabricate
        # Extraction Rules
        {_EXTRACTION_PROMPT}
        # Raw Text
        {raw_output}
        # Output
        """
    resp = await _generate_activity(messages, module, schema=LongContent)
    return parse_structured(resp, LongContent).model_dump()


# ── 长文案(对齐 _generate_long_content,两步)────────────────────────────────────
async def _generate_long_content(*, gen_prompt, event, host, language, raw_output, module) -> dict:
    if not raw_output:
        return None

    data = await _extract_with_gemini(raw_output, module)

    prompt = safe_render(
        gen_prompt["long_copywrite"],
        theme=event.get("theme"),
        startDate=event.get("time_start"),
        endDate=event.get("time_end"),
        preparationStartDate=event.get("created_at"),
        location=event.get("location"),
        attendees=event.get("attendees"),
        organization=host.get("host_name"),
        language=language,
        eventType=data.get("eventType"),
        eventFormat=data.get("eventFormat"),
        coreProblem=data.get("coreProblem"),
        keyBenefits=data.get("keyBenefits"),
        agenda=data.get("agenda"),
        speakers=data.get("speakers"),
    )
    resp = await _generate_activity(prompt, module)
    long_text = parse_structured(resp, SocialPosterRcOut)
    return {
        "text": long_text.text,
        "luma_event_title": data.get("luma_event_title"),
    }


# ── 取长文案素材(对齐后端 generated_fullplan.source / raw_text / html_content)─────
def _resolve_raw_output(plan: dict, override: str = "") -> str:
    """显式 override 优先;否则按 source 从 plan 取 raw_text / html_content。"""
    if override:
        return override
    if not plan:
        return ""
    source = plan.get("source", SOURCE_AI_EXTRACTED)
    if source == SOURCE_AI_EXTRACTED:
        # 本地 plan 的 ai_extracted 是 dict;raw_text 可能在其内或顶层。
        ai_extracted = plan.get("ai_extracted")
        if isinstance(ai_extracted, dict):
            raw = ai_extracted.get("raw_text", "")
        else:
            raw = ""
        return raw or plan.get("raw_text", "") or ""
    return plan.get("html_content", "") or ""


# ── 主生成(对齐 generate_content:短/长并行 + 异常隔离)────────────────────────────
async def generate_content(*, event, host, plan, language, raw_override="") -> dict:
    gen_prompt = load_yaml("event_description.yaml")
    raw_output = _resolve_raw_output(plan, raw_override)

    tasks = [
        ("luma_event_description_short",
         _generate_short_content(
             gen_prompt=gen_prompt, event=event, host=host,
             language=language, module="luma_event_description_short",
         )),
    ]
    if raw_output:
        tasks.append((
            "luma_event_description_long",
            _generate_long_content(
                gen_prompt=gen_prompt, event=event, host=host,
                language=language, raw_output=raw_output,
                module="luma_event_description_long",
            ),
        ))

    results = {
        "luma_event_description_short": None,
        "luma_event_description_long": None,
        "luma_event_title": None,
    }
    task_results = await asyncio.gather(*[t for _, t in tasks], return_exceptions=True)
    for (task_type, _), result in zip(tasks, task_results):
        if isinstance(result, Exception) or result is None:
            continue
        if task_type == "luma_event_description_long":
            results["luma_event_description_long"] = result.get("text")
            results["luma_event_title"] = result.get("luma_event_title")
        else:
            results[task_type] = result
    return results


def _resolve_inputs(args) -> dict:
    data = context_local.load_json("description_input") or {}
    raw_override = ""
    note = None
    if args.raw_text_file:
        try:
            with open(args.raw_text_file, "r", encoding="utf-8") as f:
                raw_override = f.read().strip()
        except OSError as e:
            # 读文件失败不崩(降级用 plan 内素材),但计入结构化 note 让上层可见,
            # 避免静默吞掉(原仅打 stderr,调用方拿不到)。
            note = f"读取 --raw-text-file({args.raw_text_file})失败:{type(e).__name__}: {e};已忽略,改用 plan 内素材。"
            print(f"[warn] {note}", file=sys.stderr)
    raw_override = raw_override or (data.get("raw_text") or "")
    return {
        "language": args.language or data.get("language"),
        "raw_override": raw_override,
        "note": note,
    }


async def _main() -> int:
    p = argparse.ArgumentParser(description="生成 Luma 活动文案(短/长/标题)")
    p.add_argument("--language", help="输出语言,如 中文 / English(缺省取 event.language)")
    p.add_argument("--raw-text-file", dest="raw_text_file",
                   help="长文案素材文件(议程/嘉宾/详情纯文本);不传则用 plan 内素材")
    args = p.parse_args()

    event = context_local.load_json("event", required=True)
    host = context_local.load_json("host", required=True)
    plan = context_local.load_json("plan", required=False) or {}
    inp = _resolve_inputs(args)
    language = inp["language"] or event.get("language", "中文")

    results = await generate_content(
        event=event, host=host, plan=plan,
        language=language, raw_override=inp["raw_override"],
    )

    has_long = bool(results.get("luma_event_description_long"))
    out = {
        "ok": True,
        "workdir": str(context_local.workdir()),
        "language": language,
        "long_content_generated": has_long,
        **results,
    }
    if not has_long:
        out["long_skipped_reason"] = (
            "未找到长文案素材(plan.ai_extracted.raw_text / plan.html_content 均为空)。"
            "只生成了短文案。需要长文案请用 --raw-text-file 提供议程/嘉宾/详情,或先用 loevent-init 注入原始描述。"
        )
    if inp.get("note"):
        out["note"] = inp["note"]

    context_local.save_json("luma", out)
    context_local.merge_into("plan", {"luma_event_description": results})
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_skill_main(_main))
