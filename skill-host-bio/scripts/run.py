#!/usr/bin/env python3
"""
skill-host-bio —— 调研并润色主办方(公司/组织)简介

对齐后端 host_profile_tools.host_profile_tool 的【两步 grounding 管线】(去 track_timing/DB/project):
  ① host_profile_google_search:llm.generate(enable_url_context=True) 读官网 URL + 搜公司信息 → 原始调研文本;
  ② generate(response_schema=self_description_polish_tool_schema) 把原始文本结构化润色成
     带【label】的公司简介(text)+ 规范公司名(host_name)。
最后用 check_and_fix_escapes(内联,逐字搬运)修字面量转义并给【】标记加换行。

降级设计(保证任意 Key 都能"加载测试"):
- 整个管线都是纯文本调用(grounding 也走默认文本模型);
- 若 grounding/网络/解析任一步失败,不让 skill 崩:返回 degraded 标记 + 原因,
  并把已拿到的中间产物(若有)一并落盘,方便 doctor 复查。

infra 改动(仅基础设施,不动 AI 逻辑):
- 后端从 Mongo 注入的 host 上下文(industry / 既有 host_profile)→ 改读本地 host.json(可选,缺也能跑);
- 任何 DB 写(update_one host_profiles)→ 改成 save_json("host") + merge_into("plan", {...});
- 去掉 @track_timing、去掉 project 路由;user_id/event_id 用默认占位(不传)。

用法:
    python skill-host-bio/scripts/run.py                       # 读 host.json/host_bio_input.json
    python skill-host-bio/scripts/run.py --website https://acme.ai \
        --org "Acme AI" --industry "AI & Technology" --language 中文 \
        --self-description "我们做面向开发者的垂直 AI 基础设施"

产物:host.json(回写 host_name/host_profile)+ merge 进 plan.json;结构化结果打印到 stdout。
结果由 Claude 按 SKILL.md「结果呈现」整理后给用户,不要直接甩 JSON。
"""

import argparse
import json
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
from engine.schemas.host_bio_models import SelfDescriptionPolish  # noqa: E402

# ── module 标签(对齐后端的两个 token 标识)──────────────────────────
GOOGLE_SEARCH_MODULE = "GoogleSearch_Event_Host_Profile"
SUMMARY_MODULE = "Event_Host_Profile"


# ── 语言后处理:逐字搬运自后端 host_profile_tools.check_and_fix_escapes ──
def check_and_fix_escapes(text: str) -> str:
    """检查文本中是否存在字面量转义字符，有则修复，并格式化【】标记"""
    patterns = {"\\n": "\n", "\\r": "\r", "\\t": "\t"}

    fixed = text
    for esc, real in patterns.items():
        fixed = fixed.replace(esc, real)

    # 在【前加 \n，】后加 \n，但跳过第一个【
    first = fixed.find("【")
    if first != -1:
        after_first = fixed[first + 1:]
        after_first = re.sub(r"】", "】\n", after_first)
        after_first = re.sub(r"【", "\n【", after_first)
        fixed = fixed[: first + 1] + after_first

    return fixed


# ── 第一步:grounding 调研(对齐后端 host_profile_google_search)──────
async def _host_profile_google_search(*, prompt: str, system_prompt: str, module: str) -> str:
    llm = get_llm_client()
    response = await llm.generate(
        module=module,
        prompt=prompt,
        system_prompt=system_prompt,
        enable_url_context=True,
    )
    if response.used_google_search:
        print("[grounding] 使用了 Google Search / URL context", file=sys.stderr)
    else:
        print("[grounding] 未触发搜索工具(可能 Key 无 grounding 权限或模型未取用)", file=sys.stderr)
    return response.text


# ── 第二步:结构化润色(对齐后端 generate_event_artice 用法)──────────
async def _summarize_profile(*, prompt: str, module: str) -> SelfDescriptionPolish:
    llm = get_llm_client()
    response = await llm.generate(
        module=module,
        prompt=prompt,
        response_schema=SelfDescriptionPolish,
    )
    return parse_structured(response, SelfDescriptionPolish)


async def host_profile_tool(*, host_website: str, language: str = "中文",
                            self_description=None,
                            organization_name=None) -> dict:
    """对齐后端 host_profile_tool,context 改为入参注入(不查 DB)。"""
    host_profile_prompt = load_yaml("host_profile.yaml")

    website_info = (
        f"请先搜索并访问该公司官网 {host_website}，获取相关信息，结合下方的公司描述进行分析。"
    )

    # user_host_profile_tool 模板含 {{organization_name}}/{{self_description}}/{{website_info}},
    # 三者全部注入,让调研 prompt 完整(后端只传了 website_info,这里补齐其余两项)。
    user_prompt = safe_render(
        host_profile_prompt["user_host_profile_tool"],
        website_info=website_info,
        organization_name=organization_name or "",
        self_description=self_description or "",
    )
    system_prompt = host_profile_prompt["system_host_profile_tool"]

    raw_search_results = await _host_profile_google_search(
        prompt=user_prompt,
        system_prompt=system_prompt,
        module=GOOGLE_SEARCH_MODULE,
    )

    prompt_summary = safe_render(
        host_profile_prompt["host_profile_tool_summary"],
        raw_search_results=raw_search_results,
        language=language,
    )

    polished = await _summarize_profile(
        prompt=prompt_summary,
        module=SUMMARY_MODULE,
    )
    result = check_and_fix_escapes(polished.text or "")

    return {
        "host_profile": result,
        "host_name": polished.host_name or "",
        "_raw_search_results": raw_search_results,
    }


def _resolve_inputs(args) -> dict:
    """优先读 host_bio_input.json,CLI 参数覆盖;再用既有 host.json 补缺省。"""
    data = context_local.load_json("host_bio_input") or {}
    host = context_local.load_json("host") or {}
    return {
        "host_website": args.website or data.get("host_website") or host.get("host_website"),
        "language": args.language or data.get("language") or host.get("language") or "中文",
        "industry": args.industry or data.get("industry") or host.get("industry"),
        "self_description": (
            args.self_description or data.get("self_description") or host.get("self_description")
        ),
        "organization_name": (
            args.org or data.get("organization_name") or host.get("host_name")
        ),
    }


async def _main() -> int:
    p = argparse.ArgumentParser(description="调研并润色主办方(公司/组织)简介")
    p.add_argument("--website", help="主办方官网 URL(必填,可改放 host_bio_input.json)")
    p.add_argument("--org", help="公司/组织名称(可选,有助于消歧)")
    p.add_argument("--industry", help="行业,如 'AI & Technology' / 'WEB 3' / 'other'")
    p.add_argument("--language", help="输出语言:中文 / English(缺省 中文)")
    p.add_argument("--self-description", dest="self_description", help="一句话自述(可选,grounding 辅助)")
    args = p.parse_args()

    inp = _resolve_inputs(args)

    if not inp["host_website"]:
        print(json.dumps({
            "ok": False,
            "error": "缺少 host_website。请用 --website 传官网 URL,"
                     "或写进工作目录的 host_bio_input.json(见 templates/host_bio_input.json)。",
        }, ensure_ascii=False, indent=2))
        return 2

    # grounding/网络/解析任一步失败 → 交给 run_skill_main 顶层兜底:
    # parse_structured 抛的解析异常 vs grounding/网络异常会带各自的类型/消息,
    # run_skill_main 统一转成结构化 {ok:false,error,message,hint} + 退出码 1。
    profile = await host_profile_tool(
        host_website=inp["host_website"],
        language=inp["language"],
        self_description=inp["self_description"],
        organization_name=inp["organization_name"],
    )

    host_name = profile.get("host_name") or inp["organization_name"] or ""
    host_profile = profile.get("host_profile") or ""

    # 回写本地上下文:host.json 累加 host_profile/industry;plan.json 同步
    # ⚠ 不覆盖 init 已写的真实 host_name —— 占位/泛域名(如 example.ai)研究出的名字
    # 会污染下游所有 skill。仅在 host.json 还没有 host_name 时才填入研究到的名字。
    existing_host = context_local.load_json("host") or {}
    host_patch = {"host_profile": host_profile}
    if not (existing_host.get("host_name") or "").strip():
        host_patch["host_name"] = host_name
    if inp["industry"]:
        host_patch["industry"] = inp["industry"]
    if inp["host_website"]:
        host_patch["host_website"] = inp["host_website"]
    context_local.merge_into("host", host_patch)
    context_local.merge_into("plan", {"host": host_patch})

    result = {
        "ok": True,
        "workdir": str(context_local.workdir()),
        "written": ["host.json(merged)", "plan.json(merged)"],
        "host_name": host_name,
        "industry": inp["industry"],
        "host_website": inp["host_website"],
        "host_profile": host_profile,
    }
    context_local.save_json("host_bio", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_skill_main(_main))
