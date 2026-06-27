#!/usr/bin/env python3
"""
skill-social —— 为活动生成社交媒体文案(小红书 / X / 社群)

对齐后端 socialpost_model._generate_socialpost 的【生成路径】(去 DB / project 路由 /
track_timing):
  组 prompt(socialpost.yaml 模板 + tones + FocusRegistry 焦点 + 540 md 知识树)
  → LLM 出结构化文案 → check_and_fix_escapes 语言后处理(转义修复 + 缺换行二次精修)。

与后端的差别(只在 infra,不在 AI 逻辑):
- 上下文不查 Mongo,改读本地 event.json / host.json / plan.json / inspiration.json;
  - event   ← user_events
  - host    ← host_profiles(industry / host_profile)
  - plan    ← generated_fullplan + eventplanner_key(guests / eventGoal / eventFlow /
              targetAudience / scene_type / activate_type;双源:ai_extracted 与 ai_generated)
  - inspiration ← hot_new(pain_points / topic_catalyst / industry_trends)
- 知识库路径从后端写死的 services/ai_tools/config/... 改为 config_path(...);
- 去掉源码里重复查一次 hot_new 的逻辑(inspiration_source 直接从已注入的 inspiration 里挑)。

无 grounding(后端本工具也不用 Google Search)。

用法:
    python skill-social/scripts/run.py --platform xiaohongshu --length medium --tone professional_tone
    python skill-social/scripts/run.py            # 读 social_input.json 兜底

平台(platform,必填):xiaohongshu | x | community
长度(length,必填)  :short | medium | long
语气(tone,必填)    :professional_tone | friendly_tone | humorous_tone | educational_tone

产物:social.json 写入工作目录,并 merge 进 plan.json;结构化结果打印到 stdout。
agent 按 SKILL.md「结果呈现」把它整理成可读格式再给用户,不要直接甩 JSON。
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from typing import Callable, Dict, List, Optional

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
from engine.model_config import industry_map, language_map  # noqa: E402
from engine.schemas.social_models import (  # noqa: E402
    SocialPosterRcOut,
    SocialPostXiaohongshuOut,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("loevent.social")

# ── 常量(对齐后端 ai_utils/constants.py)─────────────────────────
SOURCE_AI_EXTRACTED = "ai_extracted"
GUEST_STATUS_CONFIRMED = "confirmed"
GUEST_STATUS_RECOMMENDED = "recommended"

# tone 合法枚举(对齐 SKILL.md / socialpost_tones.yaml 里的 *_tone 键)
VALID_TONES = ("professional_tone", "friendly_tone", "humorous_tone", "educational_tone")

activate_map = {
    "general": "general.md",
    "community": "community.md",
    "education": "education.md",
    "investment": "investment.md",
    "technology": "technology.md",
}

# inspiration_source(用户选项)→ inspiration.json 里的字段名
field_mapping = {
    "industry_trend": "industry_trends",
    "hot_topic": "topic_catalyst",
    "painpoint": "pain_points",
}


# ============================================
# 平台配置:每个平台只声明差异点(对齐后端 PLATFORM_CONFIG)
# ============================================
PLATFORM_CONFIG = {
    "xiaohongshu": {
        "template_key": "socialpost_xiaohongshu",
        "schema": SocialPostXiaohongshuOut,
        "knowledge_path": "socialpost_xiaohongshu_tool",
        "content_field": "content",
        "has_title": True,
    },
    "x": {
        "template_key": "socialpost_x",
        "schema": SocialPosterRcOut,
        "knowledge_path": "socialpost_x_tool",
        "content_field": "text",
        "has_title": False,
    },
    "community": {
        "template_key": "socialpost_community",
        "schema": SocialPosterRcOut,
        "knowledge_path": "socialpost_community_tool",
        "content_field": "text",
        "has_title": False,
    },
}


# ============================================
# 焦点处理器注册器(对齐后端 FocusRegistry,逐字搬运)
# ============================================
class FocusRegistry:
    """焦点处理器注册器"""

    _handlers: Dict[str, Callable] = {}

    @classmethod
    def register(cls, focus_type: str):
        """装饰器:注册焦点处理器"""

        def decorator(func: Callable):
            cls._handlers[focus_type.lower()] = func
            return func

        return decorator

    @classmethod
    def get_content(cls, focus_type: str, **data) -> str:
        handler = cls._handlers.get(focus_type.lower())
        return handler(**data) if handler else ""

    @classmethod
    def get_primary(cls, focus_type: Optional[str], **data) -> str:
        return cls.get_content(focus_type, **data) if focus_type else ""

    @classmethod
    def get_secondary(cls, focus_types: Optional[List[str]], **data) -> str:
        if not focus_types:
            return ""
        return "\n\n".join(
            f"【{ft}】\n{content}"
            for ft in focus_types
            if (content := cls.get_content(ft, **data))
        )


@FocusRegistry.register("guest_profile")
def handle_guest(fullplan_data: dict = None, stage: str = "active", **_) -> str:
    if not fullplan_data:
        return ""
    guests = fullplan_data.get("guests", []) if isinstance(fullplan_data, dict) else []
    # guests 形态兼容:list[dict] / list[str] / skill-guests 写进 plan 的 dict{name:{...}} → 统一成 list[dict]
    if isinstance(guests, dict):
        guests = [{"name": n, **(v if isinstance(v, dict) else {})} for n, v in guests.items()]
    guests = [g if isinstance(g, dict) else {"name": str(g)} for g in guests]

    if stage == "warmup":
        return "\n".join(
            f"- 嘉宾线索:{g.get('position', '某行业资深人士')}"
            for g in guests
        )
    elif stage == "countdown":
        return "\n".join(
            f"- {g.get('name', '')}({g.get('position', '')})"
            for g in guests
        )
    elif stage == "lastcall":
        return ", ".join(g.get("name", "") for g in guests)
    else:
        # active(默认正式期):逐位列全嘉宾 name(position)
        return "\n".join(f"- {g.get('name', '')}({g.get('position', '')})" for g in guests)


@FocusRegistry.register("event_agenda")
def handle_agenda(eventplanner_data: dict = None, stage: str = "active", **_) -> str:
    if not eventplanner_data:
        return ""
    flow = eventplanner_data.get("eventFlow")

    if stage == "warmup":
        if isinstance(flow, list):
            return f"共{len(flow)}个议题,涵盖多个前沿方向"
        return "多个精彩议题即将揭晓"
    elif stage == "lastcall":
        if isinstance(flow, list):
            return f"{len(flow)}场深度分享"
        return ""
    else:
        if isinstance(flow, list):
            # 议程项可能是 dict(如 {time, activity}),拼成可读文本而非 dict 字面量
            return "\n".join(
                f"- {' '.join(str(v) for v in item.values() if v)}" if isinstance(item, dict) else f"- {item}"
                for item in flow
            )
        return str(flow) if flow else ""


@FocusRegistry.register("event_purpose")
def handle_purpose(eventplanner_data: dict = None, **_) -> str:
    return eventplanner_data.get("eventGoal", "") if eventplanner_data else ""


@FocusRegistry.register("basic_information")
def handle_basic_information(**_) -> str:
    return ""


# ── 知识库 wrap(对齐后端 promptGenerator.wrap_knowledge,自包含内联)──
def _wrap_knowledge(*knowledge_blocks: str, role: str = "领域知识库") -> str:
    """把知识库内容包装成带「使用说明」的引导块,供主 prompt 末尾拼接。

    过滤掉加载失败的占位串,显式声明 role + 通用使用规则;全部为空则返回 ""。
    """
    valid = [
        kb.strip()
        for kb in knowledge_blocks
        if kb and not kb.startswith("read failed:")
    ]
    if not valid:
        return ""
    body = "\n\n---\n\n".join(valid)
    return (
        f"\n\n---\n"
        f"## 📚 {role}(必须遵守)\n"
        f"以下内容是当前场景的官方知识库,请将其视为本次生成的强约束规范,"
        f"严格遵守其中给出的结构、要点和措辞建议。如与上文已声明的硬性规则冲突,"
        f"以上文为准。\n\n"
        f"{body}\n"
        f"---\n"
    )


def _load_knowledge_md(knowledge_path: str, lang: str, industry: str,
                       scene_type: str, activate_filename: str) -> str:
    """读 540 md 知识树:config/<knowledge_path>/<lang>/<industry>/<scene>/<activate>.md

    替代后端 promptGenerator.load(写死路径);文件不存在则返回 ""(不崩、不污染 prompt)。
    """
    if not activate_filename:
        return ""
    p = config_path(knowledge_path, lang, industry, scene_type, activate_filename)
    if not p.exists():
        logger.warning("[knowledge] 知识库 md 不存在,跳过: %s", p)
        return ""
    try:
        return p.read_text(encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        logger.warning("[knowledge] 读取失败 %s | %s: %s", p, type(e).__name__, e)
        return ""


def calc_event_countdown(start_date_str: str) -> dict:
    """计算当前日期(UTC+8)和距活动天数"""
    tz_utc8 = timezone(timedelta(hours=8))
    now = datetime.now(tz_utc8)
    current_date = now.strftime("%Y-%m-%d")
    try:
        start_date = datetime.strptime(str(start_date_str)[:10], "%Y-%m-%d").replace(
            tzinfo=tz_utc8
        )
        days_until = (start_date - now).days
    except (ValueError, TypeError):
        days_until = -1
    return {"current_date": current_date, "days_until_event": days_until}


async def check_and_fix_escapes(generated_content: str, tool: str) -> dict:
    """检查文本中是否存在字面量转义字符或缺少换行符,有则修复(对齐后端逐字搬运)。"""
    has_issues = False

    # 1. 修复字面量转义字符
    patterns = {"\\n": "\n", "\\r": "\r", "\\t": "\t"}
    found = {
        esc: len(re.findall(re.escape(esc), generated_content))
        for esc in patterns
        if esc in generated_content
    }
    if found:
        has_issues = True
        for esc, real in patterns.items():
            generated_content = generated_content.replace(esc, real)

    # 2. 检查是否缺少换行符(整段无换行或换行过少)
    line_count = generated_content.count("\n")
    content_length = len(generated_content)
    if content_length > 100 and line_count < 3:
        has_issues = True
        logger.info(
            "Text missing line breaks (length=%s, lines=%s), calling model to fix",
            content_length, line_count,
        )
        fix_prompt = f"""请为以下文案添加换行符,使其适合社交媒体阅读。

            核心原则:像排版一篇小红书/社群推文一样,让读者"一眼能扫完",每个视觉块只承载一个信息点。

            换行判断逻辑(按优先级):
            1. 语义切换处断开:当话题从 A 跳到 B(比如从"背景介绍"转到"活动价值",或从"正文"转到"报名信息"),中间空一行
            2. 情绪/节奏转折处断开:出现"但""然而""不只是""您将获得"等转折或引导词时,在其前面换行
            3. 信息密度高的地方拆散:一句话里塞了多个独立事实(如时间+地点+价格),拆成多行
            4. emoji 信息行(📅📍💰🔗🎯🚀🔥等):连续的 emoji 信息行归为一组,组前空一行,组内每行独立,组后空一行
            5. 列表/要点(•、-、数字序号):列表前空一行,列表项之间不加空行,列表后空一行
            6. 标签行(#xxx):标签前空一行,多组标签之间可空一行
            7. 开头 hook 和结尾 CTA 各自独立成段

            禁止事项:
            - 不改动任何文字内容(一个字都不能动)
            - 不合并、不拆分、不重组句子
            - 不添加任何标点或符号
            - 只输出处理后的文案,不要解释

            原文:
            {generated_content}"""
        try:
            llm = get_llm_client()
            fixed_response = await llm.generate(
                module=tool,
                prompt=fix_prompt,
                response_schema=SocialPosterRcOut,
            )
            fixed_data = parse_structured(fixed_response, SocialPosterRcOut)
            generated_content = fixed_data.text or generated_content
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to fix line breaks via model: %s", e)

    return {"has_issues": has_issues, "text": generated_content}


# ============================================
# 上下文解析:从本地 JSON(event/host/plan/inspiration)拼出后端等价上下文
# ============================================
def _build_event_context(event: dict, host: dict, plan: dict, inspiration: dict) -> dict:
    """把本地 JSON 组装成后端 _fetch_event_context 等价的上下文结构。

    plan.json 兼容双源:
    - ai_extracted 源:plan 里带 ai_extracted(scene_type/goal/content/...);
    - ai_generated 源(默认):plan 顶层直接带 eventplanner_data 等价字段 + guests。
    """
    userPreference = {
        "industry": host.get("industry"),
        "host_profile": host.get("host_profile"),
    }

    source = plan.get("source", "ai_generated")

    if source == SOURCE_AI_EXTRACTED:
        ai_ext = plan.get("ai_extracted", {})
        eventplanner_data = {
            "scene_type": ai_ext.get("scene_type", "Business_conferences"),
            "eventGoal": ai_ext.get("goal", ""),
            "activate_type": ai_ext.get("activate_type", "general"),
            "eventFlow": ai_ext.get("content", ""),
            "targetAudience": ai_ext.get("confirmed_audience", ""),
        }
        guests_raw = ai_ext.get("guests") or {}
        guests_list = (
            guests_raw.get(GUEST_STATUS_CONFIRMED)
            or guests_raw.get(GUEST_STATUS_RECOMMENDED)
            or []
        )
        fullplan_data = {
            "guests": [
                {"name": g.get("text", ""), "position": g.get("detail", "")}
                for g in guests_list
            ]
        }
    else:  # ai_generated 及其它源
        eventplanner_data = {
            "scene_type": plan.get("scene_type", "Business_conferences"),
            "eventGoal": plan.get("eventGoal", ""),
            "activate_type": plan.get("activate_type", "general"),
            "eventFlow": plan.get("eventFlow", ""),
            "targetAudience": plan.get("targetAudience", ""),
        }
        fullplan_data = {"guests": plan.get("guests", [])}

    return {
        "userPreference": userPreference,
        "eventplanner_data": eventplanner_data,
        "fullplan_data": fullplan_data,
        "inspiration": inspiration or {},
        "source": source,
    }


def _select_inspiration(inspiration: dict, inspiration_source: List[str]) -> dict:
    """按用户选的 inspiration_source 从 inspiration.json 里挑字段(替代后端二次查 hot_new)。"""
    if not inspiration:
        return {}
    selected = {}
    for src in inspiration_source or []:
        field = field_mapping.get(src)
        if field and field in inspiration:
            selected[field] = inspiration[field]
    return selected


# ============================================
# 主生成逻辑(对齐后端 _generate_socialpost)
# ============================================
async def generate_socialpost(
    *,
    platform: str,
    event: dict,
    host: dict,
    plan: dict,
    inspiration: dict,
    length: str,
    tone: str,
    prompt: Optional[str] = None,
    inspiration_source: Optional[List[str]] = None,
    ticket: Optional[bool] = None,
    ticket_price: Optional[str] = None,
    registration_method: Optional[List[str]] = None,
    detail_location_country: Optional[str] = None,
    detail_location_city: Optional[str] = None,
    detail_location_street: Optional[str] = None,
    detail_location_room_floor: Optional[str] = None,
    content_focus: Optional[str] = None,
    content: Optional[List[str]] = None,
    stage: Optional[str] = "active",
) -> dict:
    """统一的社交帖子生成逻辑,通过 platform 参数区分平台差异。"""
    config = PLATFORM_CONFIG[platform]
    socialpost_data = load_yaml("socialpost.yaml")
    socialpost_tones = load_yaml("socialpost_tones.yaml")

    # tone 校验:后端 tone 来自校验过的枚举,单机版从 CLI 直传,拼错会在
    # socialpost_tones[tone] 抛神秘 KeyError;这里提前给清晰报错。
    if tone not in VALID_TONES:
        raise ValueError(
            f"无效的 tone='{tone}'。可选:" + " / ".join(VALID_TONES)
        )

    ctx = _build_event_context(event, host, plan, inspiration)
    userPreference = ctx["userPreference"]
    eventplanner_data = ctx["eventplanner_data"]
    fullplan_data = ctx["fullplan_data"]
    source = ctx["source"]

    data_kwargs = {
        "eventplanner_data": eventplanner_data,
        "inspiration": ctx["inspiration"],
        "user_preference": userPreference,
        "fullplan_data": fullplan_data,
        "stage": stage,
    }

    language = event.get("language")
    industry = industry_map.get(userPreference.get("industry"))
    activate_type = eventplanner_data.get("activate_type")
    scene_type = eventplanner_data.get("scene_type")

    # inspiration_source:直接从已注入的 inspiration 里挑(去掉后端重复查 hot_new 那次)
    selected_inspiration = _select_inspiration(ctx["inspiration"], inspiration_source)

    countdown = calc_event_countdown(event.get("time_start"))
    socialpost_prompt = safe_render(
        socialpost_data[f"{length}_{config['template_key']}"],
        theme=event.get("theme"),
        event_name=event.get("event_name", ""),
        current_date=countdown["current_date"],
        days_until_event=countdown["days_until_event"],
        startDate=event.get("time_start"),
        location=event.get("location"),
        language=language,
        prompt=prompt,
        self_description=userPreference.get("host_profile"),
        organization_name=host.get("host_name"),
        tone_module=socialpost_tones[tone],
        primary_focus=FocusRegistry.get_primary(content_focus, **data_kwargs),
        secondary_focus=FocusRegistry.get_secondary(content, **data_kwargs),
        content_focus=socialpost_tones.get(content_focus, ""),
        event_purpose=eventplanner_data.get("eventGoal", ""),
        inspiration_source=selected_inspiration,
        ticket_price=ticket_price if ticket else "",
        registration_method=(
            ", ".join(registration_method) if registration_method else ""
        ),
        detail_location_country=detail_location_country or "",
        detail_location_city=detail_location_city or "",
        detail_location_street=detail_location_street or "",
        detail_location_room_floor=detail_location_room_floor or "",
        stage=socialpost_tones.get(stage, ""),
    )

    # 540 md 知识树:industry == "other" 不注入(与后端一致)
    if industry and industry != "other":
        lang = language_map.get(language) or "zh"
        knowledge_prompt = _load_knowledge_md(
            config["knowledge_path"], lang, industry, scene_type,
            activate_map.get(activate_type),
        )
        socialpost_prompt = f"{socialpost_prompt}{_wrap_knowledge(knowledge_prompt)}"

    tool_tag = f"socialpost_{platform}_tool_{tone}_{length}_{source}"
    llm = get_llm_client()
    completion = await llm.generate(
        module=tool_tag,
        prompt=socialpost_prompt,
        response_schema=config["schema"],
    )
    data = parse_structured(completion, config["schema"]).model_dump()

    content_field = config["content_field"]
    fix_result = await check_and_fix_escapes(data.get(content_field, ""), tool=tool_tag)
    if fix_result["has_issues"]:
        data[content_field] = fix_result["text"]

    response = {
        "content": data.get(content_field, ""),
        "contentLength": length,
        "content_tones": tone,
    }
    if config["has_title"]:
        response["title"] = data.get("title")
    return response


# ============================================
# 输入解析 + CLI
# ============================================
def _resolve_inputs(args) -> dict:
    """优先读 social_input.json,CLI 参数覆盖;给出合理缺省。"""
    data = context_local.load_json("social_input") or {}

    def pick(cli_val, key, default=None):
        return cli_val if cli_val is not None else data.get(key, default)

    inspiration_source = args.inspiration_source or data.get("inspiration_source") or []
    if isinstance(inspiration_source, str):
        inspiration_source = [inspiration_source]
    registration_method = args.registration_method or data.get("registration_method") or []
    if isinstance(registration_method, str):
        registration_method = [registration_method]
    content = args.content or data.get("content") or []
    if isinstance(content, str):
        content = [content]

    return {
        "platform": pick(args.platform, "platform"),
        "length": pick(args.length, "length", "medium"),
        "tone": pick(args.tone, "tone", "professional_tone"),
        "prompt": pick(args.prompt, "prompt"),
        "stage": pick(args.stage, "stage", "active"),
        "content_focus": pick(args.content_focus, "content_focus"),
        "content": content,
        "inspiration_source": inspiration_source,
        "ticket": pick(args.ticket, "ticket"),
        "ticket_price": pick(args.ticket_price, "ticket_price"),
        "registration_method": registration_method,
        "detail_location_country": pick(args.detail_location_country, "detail_location_country"),
        "detail_location_city": pick(args.detail_location_city, "detail_location_city"),
        "detail_location_street": pick(args.detail_location_street, "detail_location_street"),
        "detail_location_room_floor": pick(args.detail_location_room_floor, "detail_location_room_floor"),
    }


async def _main() -> int:
    p = argparse.ArgumentParser(description="为活动生成社交媒体文案(小红书 / X / 社群)")
    p.add_argument("--platform", choices=list(PLATFORM_CONFIG.keys()),
                   help="平台: xiaohongshu | x | community")
    p.add_argument("--length", choices=["short", "medium", "long"], help="文案长度")
    p.add_argument("--tone", help="语气: professional_tone | friendly_tone | humorous_tone | educational_tone")
    p.add_argument("--prompt", help="额外的用户方向描述")
    p.add_argument("--stage", choices=["warmup", "active", "countdown", "lastcall"],
                   help="活动阶段(影响嘉宾/议程的呈现方式)")
    p.add_argument("--content-focus", dest="content_focus",
                   help="主焦点: guest_profile | event_agenda | event_purpose | basic_information")
    p.add_argument("--content", action="append",
                   help="次焦点(可多次): guest_profile / event_agenda / event_purpose")
    p.add_argument("--inspiration-source", dest="inspiration_source", action="append",
                   help="灵感来源(可多次): industry_trend / hot_topic / painpoint(需 inspiration.json)")
    p.add_argument("--ticket", action="store_true", default=None, help="是否售票(带上则填票价)")
    p.add_argument("--ticket-price", dest="ticket_price", help="票价描述")
    p.add_argument("--registration-method", dest="registration_method", action="append",
                   help="报名方式(可多次)")
    p.add_argument("--detail-location-country", dest="detail_location_country")
    p.add_argument("--detail-location-city", dest="detail_location_city")
    p.add_argument("--detail-location-street", dest="detail_location_street")
    p.add_argument("--detail-location-room-floor", dest="detail_location_room_floor")
    args = p.parse_args()

    event = context_local.load_json("event", required=True)
    host = context_local.load_json("host", required=True)
    plan = context_local.load_json("plan") or {}
    inspiration = context_local.load_json("inspiration") or {}

    inputs = _resolve_inputs(args)
    platform = inputs.pop("platform")
    if not platform:
        print(json.dumps({
            "ok": False,
            "error": f"缺少必填字段:platform(平台无安全默认,猜哪个平台必错)。"
                     f"请用 --platform 传入 {list(PLATFORM_CONFIG.keys())} 之一,或写进 social_input.json;"
                     f"建议先用 AskUserQuestion 问用户要发哪个平台再跑。",
        }, ensure_ascii=False, indent=2))
        return 2
    if platform not in PLATFORM_CONFIG:
        print(json.dumps({
            "ok": False,
            "error": f"未知 platform={platform!r},应为 {list(PLATFORM_CONFIG.keys())}",
        }, ensure_ascii=False, indent=2))
        return 2

    # LLM / 缺字段 等异常交给 run_skill_main 统一兜底(结构化 {ok:false} + 退出码)。
    result = await generate_socialpost(
        platform=platform, event=event, host=host, plan=plan,
        inspiration=inspiration, **inputs,
    )

    out = {
        "ok": True,
        "workdir": str(context_local.workdir()),
        "platform": platform,
        "written": ["social.json", "plan.json(merged)"],
        "social": result,
    }
    context_local.save_json("social", out)
    context_local.merge_into("plan", {"social": {"platform": platform, **result}})
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_skill_main(_main))
