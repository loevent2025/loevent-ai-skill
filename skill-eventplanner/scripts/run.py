#!/usr/bin/env python3
"""
skill-eventplanner —— 把一场活动写成一份完整的活动策划方案(6 个章节)

这是后端 eventplanner_mode（外层 node1..6）+ module_tools/eventplanner_tools
（内层 node_1..6）的【干净化重写】。语义对齐原管线，但做了四刀清理：

  1) 节点 = 纯函数:def node_N(state) -> {section + 该节点传话字段}。
     节点内不查 DB、不读写文件,只 render prompt + 调一次 LLM。
  2) 砍二次 LLM + 砍 HTML-as-state:原管线"一次出 HTML → 存 → 第二次 LLM 抽 JSON"。
     这里每节点【一次】llm.generate(response_schema=合并 schema),同时拿到
     section 正文(Markdown)和传话字段。不复用 full_nodeN(那只是窄传话字段),
     而是新建合并 schema = {section + full_nodeN 字段}。
  3) PlanState 显式串:runner 持有一个 state dict,按
     node_1 → node_2 → node_3 → node_5 → node_6 顺序跑,
     每个节点的传话字段 merge 回 state 供下游读。
  4) 知识库收口:KnowledgeResolver(node, language, industry, scene) 读
     config_path("node_X", lang, industry, scene, "general.md");industry='other' 退化(跳过)。

上下文来源(pre 阶段已被现有 skill 覆盖,这里只读本地 JSON):
  event.json  —— skill-init:event_name/theme/time_start/time_end/location/attendees/language
  host.json   —— skill-init:host_name(organization)/industry/host_profile(self_description)
  plan.json   —— skill-init/company 写 scene_type/event_scale;
                 skill-audience 写 audience(primary/secondary/extended.{audience,painpoint});
                 skill-company 写 company.{brand_dna,competitor,trend_forward}(三张 vibe 卡)。
  用户输入    —— eventplanner_input.json 或 CLI:selected_vibe / event_goal /
                 prompt_objective / GTMmatrix / preparation_start_date / user_input。

用法:
    python run.py                          # 读工作目录 event/host/plan + eventplanner_input.json
    python run.py --selected-vibe competitor --goal product \
        --objective "拉新开发者并转化框架试用" --prep-date 2026-07-01

产物:eventplan.json 写入工作目录,并 merge 进 plan.json;结构化结果打印到 stdout。
agent 按 SKILL.md「结果呈现」把 6 个 section 拼成可读方案再给用户,不要直接甩 JSON。
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Optional, TypedDict

_BUNDLE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.insert(0, _BUNDLE_ROOT)

from engine import get_llm_client, load_yaml, safe_render, context_local  # noqa: E402
from engine.config_loader import config_path  # noqa: E402
from engine.model_config import industry_map, language_map  # noqa: E402
from engine.schemas.eventplanner_models import (  # noqa: E402
    Node1Out,
    Node2Out,
    Node3Out,
    Node5Out,
    Node6Out,
)

logger = logging.getLogger("loevent.eventplanner")

EVENTPLANNER_YAML = load_yaml("eventplanner.yaml")

# selected_vibe 既接受 init/pre 阶段那套带连字符的值(brand-dna/competitor/trend-forward),
# 也接受 plan.company 里那套下划线 key(brand_dna/competitor/trend_forward),统一映射到后者。
_VIBE_MAP = {
    "brand-dna": "brand_dna",
    "competitor": "competitor",
    "trend-forward": "trend_forward",
    "brand_dna": "brand_dna",
    "trend_forward": "trend_forward",
}

# ── node_2 章节标题本地化(对齐后端 node_2 的 node2_titles,喂给 system_node_2 的 jinja 占位)──
_NODE2_TITLES = {
    "zh": {
        "title_agenda": "活动流程内容",
        "title_attendee_profile": "活动受众画像",
        "title_guest_speaker": "活动受邀嘉宾",
    },
    "en": {
        "title_agenda": "Event Agenda",
        "title_attendee_profile": "Event Attendee Profile",
        "title_guest_speaker": "Event Guest Speaker Proposal",
    },
}

# 覆盖指令:追加在每个 user_prompt 末尾,把"出 HTML"扭成"出符合合并 schema 的 JSON"。
# 这样一次调用同时拿到 section 正文(Markdown) + 传话字段,省掉第二次抽取 LLM。
_OVERRIDE_INSTRUCTION = (
    "\n\n---\n\n"
    "## Output Override (highest priority)\n\n"
    "Ignore any output-format instruction in the system prompt that asks for HTML, "
    "`<div class=\"section\">`, inline styles, or any markup. "
    "Return ONLY a JSON object that conforms to the provided JSON schema. "
    "Put the complete chapter body into the `section` field as plain **Markdown** "
    "(headings, tables, lists allowed; NO HTML tags). "
    "Fill every other field in the schema with the corresponding structured value. "
    "All natural-language text must be in: {language}.\n"
)


# ─────────────────────────────────────────────────────────────
# 结构化输出契约 = Pydantic 模型(engine/schemas/eventplanner_models.py)。
# 每节点一次 llm.generate(response_schema=NodeNOut),用 model_validate_json 解析。
# PlanState 是异构容器(dict + KnowledgeResolver + 运行中动态 merge 的传话字段),
# 用 TypedDict 做静态类型提示(运行期仍是 dict,与 .get/.update 零摩擦);不做成 BaseModel。
# ─────────────────────────────────────────────────────────────
class PlanState(TypedDict, total=False):
    event: dict
    host: dict
    language: str
    industry: str
    event_scale: str
    scene_type: Optional[str]
    audience: dict
    vibe: dict
    user_inputs: dict
    knowledge: object
    # 上游节点 merge 进来的传话字段(运行中逐步出现):
    eventType: str
    eventTone: str
    shortTermGoals: str
    midTermGoals: str
    organizerProfile: str
    eventGoal: str
    twitterMetrics: str
    targetAudience: str
    eventFlow: str
    venueInfo: str
    sponsorship: str
    promotionMarketing: str


# ─────────────────────────────────────────────────────────────
# 知识库收口:对齐后端 promptGenerator.load 的路径
#   config_path("node_X", lang, industry, scene, "general.md")
#   industry == 'other' → 退化:返回 "",节点只用 system prompt。
# node_3 的 city.md(后端 node_3 里 event_record.get("city") 分支)是死代码:
#   eventplanner_key 从不写 city,该分支永不触发 —— 本 skill【不实现】city.md。
# ─────────────────────────────────────────────────────────────
class KnowledgeResolver:
    def __init__(self, *, language: str, industry: str):
        self.lang = language_map.get(language) or "zh"
        self.industry = industry  # 已是 industry_map 映射后的值(ai_commercial/web3/other)

    def load(self, *, node: str, scene: str) -> str:
        """读 engine/config/<node>/<lang>/<industry>/<scene>/general.md;退化时返回 ''。"""
        if self.industry == "other" or not scene:
            logger.debug("KB skip(退化): node=%s industry=%s scene=%s", node, self.industry, scene)
            return ""  # 退化:跳过知识库
        p = config_path(node, self.lang, self.industry, scene, "general.md")
        if p.exists():
            logger.debug("KB hit: %s", p)
            return p.read_text(encoding="utf-8")
        # 路径不存在(区别于"有意退化")—— 多半是 scene_type 大小写/拼写不对
        logger.warning("KB miss(路径不存在,scene_type 可能拼错): %s", p)
        return ""


def _wrap_knowledge(knowledge: str) -> str:
    """把知识块拼到 system prompt 后(对齐后端 promptGenerator.wrap_knowledge 的语义)。"""
    if not knowledge:
        return ""
    return (
        "\n\n---\n\n## Industry Knowledge Base (authoritative reference)\n\n"
        f"{knowledge}\n"
    )


# ─────────────────────────────────────────────────────────────
# 一次 LLM 调用:render user_prompt(末尾追加覆盖指令)+ system(scale system + 知识块)
#   → response_schema=合并 schema → 解析出 {section + 传话字段}
# ─────────────────────────────────────────────────────────────
def _strip_json_fence(text: str) -> str:
    """剥 ```json ... ``` 围栏 / 截取首个 {...},容忍 fallback 模型偶发的非纯 JSON。"""
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t[:4].lower() == "json":
            t = t[4:]
    i, j = t.find("{"), t.rfind("}")
    return t[i:j + 1] if 0 <= i < j else t


def _parse_node_output(resp, model_cls):
    """把 LLM 文本校验成 model_cls 实例;失败抛带 finish_reason 的清晰异常(交节点级降级)。"""
    text = resp.text or ""
    try:
        return model_cls.model_validate_json(text)
    except Exception:
        try:
            return model_cls.model_validate_json(_strip_json_fence(text))
        except Exception as e:
            fr = getattr(resp, "finish_reason", None)
            hint = "(正文超长被截断,建议调小章节或重跑)" if fr == "MAX_TOKENS" else ""
            raise RuntimeError(
                f"输出解析失败 finish_reason={fr}{hint}: {type(e).__name__}: {e}"
            ) from e


async def _run_node(
    *,
    user_template_key: str,
    system_prompt: str,
    knowledge: str,
    model_cls,
    language: str,
    user_kwargs: dict,
    module: str,
) -> dict:
    user_prompt = safe_render(EVENTPLANNER_YAML[user_template_key], **user_kwargs)
    user_prompt += _OVERRIDE_INSTRUCTION.format(language=language)
    full_system = f"{system_prompt}{_wrap_knowledge(knowledge)}"

    llm = get_llm_client()
    resp = await llm.generate(
        module=module,
        prompt=user_prompt,
        system_prompt=full_system,
        response_schema=model_cls,
        max_output_tokens=65536,
    )
    # Pydantic 校验 → 类型化实例;.model_dump() 转 dict 供 runner 弹 section / merge 传话字段
    return _parse_node_output(resp, model_cls).model_dump()


# ─────────────────────────────────────────────────────────────
# 节点 = 纯函数:吃 PlanState(state),吐 {section + 该节点传话字段}
#   state 字段约定(runner 维护):
#     event/host(基础信息)、event_scale/scene_type(分类)、
#     industry(已映射)、language(原值)、knowledge(KnowledgeResolver)、
#     audience(三层 + 痛点)、vibe(选中那张 vibe 卡)、user_inputs(目标/GTM/prep/user_input)、
#     以及上游节点 merge 进来的传话字段(eventType/eventTone/...)。
# ─────────────────────────────────────────────────────────────
async def node_1(state: dict) -> dict:
    ev, host, ui = state["event"], state["host"], state["user_inputs"]
    vibe = state["vibe"]
    gtm = ui.get("GTMmatrix") or {}
    user_kwargs = dict(
        event_name=ev.get("event_name"),
        theme=ev.get("theme"),
        startDate=ev.get("time_start"),
        endDate=ev.get("time_end"),
        preparationStartDate=ui.get("preparation_start_date"),
        location=ev.get("location"),
        attendees=ev.get("attendees"),
        organization=host.get("host_name"),
        self_description=host.get("host_profile"),
        language=state["language"],
        slogan=vibe.get("slogan"),
        personWhoCome=_audience_summary(state["audience"]),
        promotionGoalType=ui.get("event_goal"),
        objective=ui.get("prompt_objective"),
        gtmGrowthMode=_gtm_part(gtm, "growth_mode"),
        gtmLifecycleFocus=_gtm_part(gtm, "lifecycle"),
        content=ui.get("content"),
        user_input=ui.get("user_input"),
    )
    system_prompt = EVENTPLANNER_YAML[f"system_{state['event_scale']}_node_1"]
    knowledge = state["knowledge"].load(node="node_1", scene=state["scene_type"])
    return await _run_node(
        user_template_key="user_node_1",
        system_prompt=system_prompt,
        knowledge=knowledge,
        model_cls=Node1Out,
        language=state["language"],
        user_kwargs=user_kwargs,
        module="eventplanner_node_1",
    )


async def node_2(state: dict) -> dict:
    # 读 node_1 的传话字段:eventType / shortTermGoals / midTermGoals / organizerProfile
    ev, host, ui = state["event"], state["host"], state["user_inputs"]
    vibe, aud = state["vibe"], state["audience"]
    gtm = ui.get("GTMmatrix") or {}
    user_kwargs = dict(
        event_name=ev.get("event_name"),
        theme=ev.get("theme"),
        startDate=ev.get("time_start"),
        endDate=ev.get("time_end"),
        location=ev.get("location"),
        attendees=ev.get("attendees"),
        organization=host.get("host_name"),
        self_description=host.get("host_profile"),
        language=state["language"],
        content=ui.get("content"),
        eventType=state.get("eventType"),
        shortTermGoals=state.get("shortTermGoals"),
        midTermGoals=state.get("midTermGoals"),
        organizerProfile=state.get("organizerProfile"),
        coreAudience=_layer(aud, "primary"),
        secondaryAudience=_layer(aud, "secondary"),
        extendedAudience=_layer(aud, "extended"),
        promotionGoalType=ui.get("event_goal"),
        objective=ui.get("prompt_objective"),
        gtmGrowthMode=_gtm_part(gtm, "growth_mode"),
        gtmLifecycleFocus=_gtm_part(gtm, "lifecycle"),
        featuredInteraction=vibe.get("interaction"),
        featuredGuest=vibe.get("cohost_guest"),
        # 后端 node_2 会先做一次 Google Search 拿灵感再喂进来;干净版不引入二次搜索,留空容忍。
        interaction_search_results=None,
        user_input=ui.get("user_input"),
    )
    titles = _NODE2_TITLES.get(language_map.get(state["language"]) or "zh", _NODE2_TITLES["en"])
    system_prompt = safe_render(
        EVENTPLANNER_YAML[f"system_{state['event_scale']}_node_2"], **titles
    )
    knowledge = state["knowledge"].load(node="node_2", scene=state["scene_type"])
    return await _run_node(
        user_template_key="user_node_2",
        system_prompt=system_prompt,
        knowledge=knowledge,
        model_cls=Node2Out,
        language=state["language"],
        user_kwargs=user_kwargs,
        module="eventplanner_node_2",
    )


async def node_3(state: dict) -> dict:
    # 读 node_1 + node_2 的传话字段:eventType / eventTone / targetAudience
    ev, host, ui = state["event"], state["host"], state["user_inputs"]
    vibe, aud = state["vibe"], state["audience"]
    user_kwargs = dict(
        event_name=ev.get("event_name"),
        theme=ev.get("theme"),
        startDate=ev.get("time_start"),
        endDate=ev.get("time_end"),
        location=ev.get("location"),
        attendees=ev.get("attendees"),
        organization=host.get("host_name"),
        self_description=host.get("host_profile"),
        language=state["language"],
        content=ui.get("content"),
        eventType=state.get("eventType"),
        eventTone=state.get("eventTone"),
        coreAudience=_layer(aud, "primary"),
        secondaryAudience=_layer(aud, "secondary"),
        extendedAudience=_layer(aud, "extended"),
        # 选中 vibe 卡作为"用户选定方向卡";sceneDimensions 后端走 city 死代码,这里留空容忍。
        selectedCard=vibe,
        sceneDimensions=None,
        user_input=ui.get("user_input"),
    )
    system_prompt = EVENTPLANNER_YAML["system_node_3"]  # node_3 不分 scale
    knowledge = state["knowledge"].load(node="node_3", scene=state["scene_type"])
    # 注:后端 node_3 还有 city.md 分支(event_record.get("city")),但 eventplanner_key
    #     从不写 city,该分支恒不触发 —— 死代码,本 skill 不实现。
    return await _run_node(
        user_template_key="user_node_3",
        system_prompt=system_prompt,
        knowledge=knowledge,
        model_cls=Node3Out,
        language=state["language"],
        user_kwargs=user_kwargs,
        module="eventplanner_node_3",
    )


async def node_5(state: dict) -> dict:
    # 读 node1/2/3 的传话字段:eventType / organizerProfile / eventFlow / venueInfo
    ev, host, ui = state["event"], state["host"], state["user_inputs"]
    user_kwargs = dict(
        event_name=ev.get("event_name"),
        theme=ev.get("theme"),
        location=ev.get("location"),
        attendees=ev.get("attendees"),
        organization=host.get("host_name"),
        self_description=host.get("host_profile"),
        language=state["language"],
        content=ui.get("content"),
        eventType=state.get("eventType"),
        organizerProfile=state.get("organizerProfile"),
        eventFlow=state.get("eventFlow"),
        venueInfo=state.get("venueInfo"),
        personWhoCome=_audience_summary(state["audience"]),
        user_input=ui.get("user_input"),
    )
    system_prompt = EVENTPLANNER_YAML[f"system_{state['event_scale']}_node_5"]
    knowledge = state["knowledge"].load(node="node_5", scene=state["scene_type"])
    return await _run_node(
        user_template_key="user_node_5",
        system_prompt=system_prompt,
        knowledge=knowledge,
        model_cls=Node5Out,
        language=state["language"],
        user_kwargs=user_kwargs,
        module="eventplanner_node_5",
    )


async def node_6(state: dict) -> dict:
    # 读 node_1 的传话字段:eventType / eventGoal / twitterMetrics(+ targetAudience 来自 node_2)
    ev, host, ui = state["event"], state["host"], state["user_inputs"]
    gtm = ui.get("GTMmatrix") or {}
    user_kwargs = dict(
        event_name=ev.get("event_name"),
        theme=ev.get("theme"),
        startDate=ev.get("time_start"),
        location=ev.get("location"),
        attendees=ev.get("attendees"),
        organization=host.get("host_name"),
        self_description=host.get("host_profile"),
        language=state["language"],
        content=ui.get("content"),
        eventType=state.get("eventType"),
        eventGoal=state.get("eventGoal"),
        twitterMetrics=state.get("twitterMetrics"),
        personWhoCome=state.get("targetAudience") or _audience_summary(state["audience"]),
        promotionGoalType=ui.get("event_goal"),
        objective=ui.get("prompt_objective"),
        gtmGrowthMode=_gtm_part(gtm, "growth_mode"),
        gtmLifecycleFocus=_gtm_part(gtm, "lifecycle"),
        user_input=ui.get("user_input"),
    )
    system_prompt = EVENTPLANNER_YAML[f"system_{state['event_scale']}_node_6"]
    knowledge = state["knowledge"].load(node="node_6", scene=state["scene_type"])
    # industry == 'other' 时后端 node_6 额外拼 platform_localization_other;干净版保留这一退化补强。
    if state["industry"] == "other":
        system_prompt = f"{system_prompt}\n\n{EVENTPLANNER_YAML['platform_localization_other']}"
    return await _run_node(
        user_template_key="user_node_6",
        system_prompt=system_prompt,
        knowledge=knowledge,
        model_cls=Node6Out,
        language=state["language"],
        user_kwargs=user_kwargs,
        module="eventplanner_node_6",
    )


# ─────────────────────────────────────────────────────────────
# 受众 / GTM 小工具
# ─────────────────────────────────────────────────────────────
def _layer(audience: dict, key: str) -> str:
    layer = (audience or {}).get(key) or {}
    a = layer.get("audience", "")
    pp = layer.get("painpoint")
    return f"{a}（痛点:{pp}）" if pp else a


def _audience_summary(audience: dict) -> str:
    parts = [_layer(audience, k) for k in ("primary", "secondary", "extended")]
    return " / ".join([p for p in parts if p]) or ""


def _gtm_part(gtm: dict, key: str):
    part = (gtm or {}).get(key) or {}
    label, value = part.get("label"), part.get("value")
    if label is None and value is None:
        return None
    return f"{label}（{value}）" if label is not None else value


# ─────────────────────────────────────────────────────────────
# vibe 卡解析 + 降级:缺 plan.company 的三张卡 → 占位卡,不崩
# ─────────────────────────────────────────────────────────────
_PLACEHOLDER_VIBE = {
    "title": "（未跑 loevent-company）",
    "slogan": "",
    "location": "",
    "interaction": "",
    "cohost_guest": "",
}


def _resolve_vibe(plan: dict, selected_vibe) -> tuple:
    """返回 (vibe_card, degraded_note|None)。缺卡时退化用占位卡。"""
    company = (plan or {}).get("company") or {}
    cards = {k: company.get(k) for k in ("brand_dna", "competitor", "trend_forward")}
    have = {k: v for k, v in cards.items() if v}
    if not have:
        return dict(_PLACEHOLDER_VIBE), (
            "缺少 company vibe 卡(plan.company 没有 brand_dna/competitor/trend_forward)。"
            "建议先跑 loevent-company 生成三套策略卡并让用户选一张;本次用占位卡降级生成,"
            "slogan/互动/嘉宾方向等会偏空。"
        )
    key = _VIBE_MAP.get(selected_vibe)
    if key and have.get(key):
        return have[key], None
    # selected_vibe 缺失/无效 → 取第一张可用卡,提示用户应明确选一张
    fallback_key = next(iter(have))
    return have[fallback_key], (
        f"未指定有效 selected_vibe(收到 {selected_vibe!r}),已默认用 '{fallback_key}' 卡。"
        "建议让用户在 brand_dna / competitor / trend_forward 中明确选一张(人机门)。"
    )


# ─────────────────────────────────────────────────────────────
# 输入解析:eventplanner_input.json + CLI 覆盖
# ─────────────────────────────────────────────────────────────
def _resolve_inputs(args) -> dict:
    data = context_local.load_json("eventplanner_input") or {}
    gtm = data.get("GTMmatrix")
    if (args.growth_value is not None or args.lifecycle_value is not None) and gtm is None:
        gtm = {}
    if args.growth_value is not None:
        gtm = {**(gtm or {}), "growth_mode": {"label": args.growth_label or "获取", "value": args.growth_value}}
    if args.lifecycle_value is not None:
        gtm = {**(gtm or {}), "lifecycle": {"label": args.lifecycle_label or "早期", "value": args.lifecycle_value}}
    return {
        "selected_vibe": args.selected_vibe or data.get("selected_vibe"),
        "event_goal": args.goal or data.get("event_goal", "product"),
        "prompt_objective": args.objective or data.get("prompt_objective", ""),
        "GTMmatrix": gtm or data.get("GTMmatrix"),
        "preparation_start_date": args.prep_date or data.get("preparation_start_date"),
        "user_input": args.user_input or data.get("user_input"),
        # content:可选的"用户提供参考资料"(对齐后端 user_prompt 的 {{content}});默认空。
        "content": data.get("content"),
    }


# ─────────────────────────────────────────────────────────────
# Runner:显式 PlanState,顺序 node_1 → 2 → 3 → 5 → 6,每步 merge 传话字段回 state
# ─────────────────────────────────────────────────────────────
async def run_eventplan(*, event: dict, host: dict, plan: dict, user_inputs: dict) -> dict:
    language = event.get("language") or "中文"
    industry = industry_map.get(host.get("industry"), "other")
    # event_scale 白名单:yaml 只有 large/medium/small 三档,非标准值会让 system_{scale}_node_N KeyError
    raw_scale = plan.get("event_scale")
    event_scale = raw_scale if raw_scale in ("large", "medium", "small") else "medium"
    scene_type = plan.get("scene_type")
    audience = plan.get("audience") or {}

    vibe, vibe_note = _resolve_vibe(plan, user_inputs.get("selected_vibe"))

    notes = []
    if vibe_note:
        notes.append(vibe_note)
    if raw_scale and raw_scale not in ("large", "medium", "small"):
        notes.append(f"未识别的 event_scale={raw_scale!r},已退化为 'medium'。")
    if not audience:
        notes.append(
            "缺少受众画像(plan.audience)。建议先跑 loevent-audience;本次受众相关字段会偏空。"
        )
    if not plan.get("scene_type"):
        notes.append(
            "plan 缺 scene_type/event_scale(通常由 loevent-init/loevent-company 写)。"
            "已用默认 event_scale='medium',知识库按行业/场景退化跳过。"
        )

    state = {
        "event": event,
        "host": host,
        "language": language,
        "industry": industry,
        "event_scale": event_scale,
        "scene_type": scene_type,
        "audience": audience,
        "vibe": vibe,
        "user_inputs": user_inputs,
        "knowledge": KnowledgeResolver(language=language, industry=industry),
    }

    nodes_out = {}
    ok_count = 0
    # 顺序串:node_4(timeline)是独立 skill,这里不生成。
    for node_name, fn in (
        ("node_1", node_1),
        ("node_2", node_2),
        ("node_3", node_3),
        ("node_5", node_5),
        ("node_6", node_6),
    ):
        logger.info("running %s ...", node_name)
        try:
            result = await fn(state)
            section = result.pop("section", "")
            passthrough = result  # 剩余即传话字段
            nodes_out[node_name] = {"section": section, "fields": passthrough}
            # 传话字段 merge 回 state 供下游读
            state.update({k: v for k, v in passthrough.items() if v is not None})
            ok_count += 1
        except Exception as e:
            # 节点失败隔离:坏一章不连坐,继续跑下游(下游读不到传话字段会容忍为空)
            logger.error("%s failed: %s", node_name, e)
            nodes_out[node_name] = {"section": None, "fields": {}, "error": f"{type(e).__name__}: {e}"}
            notes.append(f"{node_name} 生成失败({type(e).__name__}),其余章节仍照常输出;建议单独重跑该章。")

    # node_4(timeline):本 skill 不生成。plan 已有则带上,否则提示用独立 skill。
    timeline = plan.get("timeline")
    if timeline:
        nodes_out["node_4"] = {"section": None, "fields": {"timeline": timeline}, "from": "plan.timeline"}
    else:
        notes.append("时间线(节点4)未生成:请用 loevent-timeline 单独生成关键任务时间线。")

    # 合并结构化字段(各节点传话字段汇总,供下游/追溯)
    merged_fields = {}
    for n in nodes_out.values():
        merged_fields.update(n.get("fields") or {})

    return {
        "nodes": nodes_out,
        "fields": merged_fields,
        "ok_count": ok_count,
        "event_scale": event_scale,
        "scene_type": scene_type,
        "selected_vibe": _VIBE_MAP.get(user_inputs.get("selected_vibe")),
        "notes": notes,
    }


async def _main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    p = argparse.ArgumentParser(description="把活动写成一份完整活动策划方案(6 章节)")
    p.add_argument("--selected-vibe", dest="selected_vibe",
                   help="选定的 vibe 卡: brand_dna | competitor | trend_forward(人机门,由 agent 收集)")
    p.add_argument("--goal", help="event_goal: product | ecosystem | brand")
    p.add_argument("--objective", help="一句话目标描述")
    p.add_argument("--prep-date", dest="prep_date", help="筹备开始日期,如 2026-07-01")
    p.add_argument("--user-input", dest="user_input", help="额外的用户要求(可选)")
    p.add_argument("--growth-label", dest="growth_label")
    p.add_argument("--growth-value", dest="growth_value", type=int)
    p.add_argument("--lifecycle-label", dest="lifecycle_label")
    p.add_argument("--lifecycle-value", dest="lifecycle_value", type=int)
    args = p.parse_args()

    try:
        event = context_local.load_json("event", required=True)
        host = context_local.load_json("host", required=True)
        plan = context_local.load_json("plan") or {}
        user_inputs = _resolve_inputs(args)
    except FileNotFoundError as e:
        print(json.dumps({"ok": False, "error": "MissingContext", "message": str(e),
                          "hint": "请先在当前工作目录跑 loevent-init,生成 event.json/host.json/plan.json。"},
                         ensure_ascii=False, indent=2))
        return 2
    except ValueError as e:
        print(json.dumps({"ok": False, "error": "BadContext", "message": str(e),
                          "hint": "上下文 JSON 损坏(event/host/plan/eventplanner_input);修正或删除后重跑 loevent-init。"},
                         ensure_ascii=False, indent=2))
        return 2

    # 人机门:company 已出 vibe 卡但用户没选/选错 → 硬挡,让 agent 用 AskUserQuestion 让用户明确选一张,
    # 别静默替用户取第一张卡出整份方案。卡完全没有(没跑 company)是另一回事,走 run_eventplan 内的占位降级。
    company = (plan or {}).get("company") or {}
    available_vibes = [k for k in ("brand_dna", "competitor", "trend_forward") if company.get(k)]
    selected_vibe = user_inputs.get("selected_vibe")
    if available_vibes and _VIBE_MAP.get(selected_vibe) not in available_vibes:
        print(json.dumps({
            "ok": False,
            "error": f"缺少必选字段:selected_vibe(策略 vibe 卡,人机门,无安全默认)。"
                     f"company 已生成可选卡 {available_vibes},请让用户从中明确选一张,"
                     f"用 --selected-vibe 传入或写进 eventplanner_input.json;别替用户默认选第一张。",
        }, ensure_ascii=False, indent=2))
        return 2

    try:
        result = await run_eventplan(event=event, host=host, plan=plan, user_inputs=user_inputs)
    except Exception as e:
        print(json.dumps({"ok": False, "error": type(e).__name__, "message": str(e),
                          "hint": "可能是 Key 无权限/配额或网络问题;先跑 python engine/doctor.py 自检后重试。"},
                         ensure_ascii=False, indent=2))
        return 1

    context_local.save_json("eventplan", result)
    written = ["eventplan.json"]
    ok_count = result.get("ok_count", 0)
    if ok_count > 0:
        # 至少一章成功才 merge,避免全失败的空壳污染 plan.json 误导下游
        context_local.merge_into("plan", {"eventplan": result})
        written.append("plan.json(merged)")
    else:
        result.setdefault("notes", []).append(
            "全部章节生成失败,未写入 plan.json(避免空壳污染);请检查 Key/网络后重跑。"
        )

    out = {
        "ok": ok_count > 0,
        "workdir": str(context_local.workdir()),
        "written": written,
        "eventplan": result,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if ok_count > 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(_main()))
    except KeyboardInterrupt:
        raise SystemExit(130)
