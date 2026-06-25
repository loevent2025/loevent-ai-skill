#!/usr/bin/env python3
"""
skill-poster —— 生成活动海报图

对齐后端 poster_model_2.generate_poster 的【生成路径】(不含 OCR 精修/DB):
  build_generation_prompt(style 知识库 + 活动信息 → LLM 出结构化 prompt → 主题二次精修)
  → generate_image → 存 PNG。

降级设计(关键,保证任何 Key 都能"加载测试"):
- 文本部分(组 prompt)在任何文本档 Key 上都能跑;
- 图像生成需"计费档"Key(gemini-3-pro-image)。若 Key 无图像档,
  **脚本仍会产出并保存 generation_prompt**,只把图像那步标记为降级失败,
  不让整个 skill 崩。这样 doctor 报降级时,文本管线照样可验证。

用法:
    python skill-poster/scripts/run.py                 # 读 event.json/host.json/poster_input.json
    python skill-poster/scripts/run.py --style minimalist --ratio 9:16 --resolution 2K \
        --prompt "强调开发者社区氛围" --color "#1a1a2e"

产物:poster_<n>.png + poster.json(含 generation_prompt / 图像状态)写入工作目录。
结果由 Claude 按 SKILL.md「结果呈现」整理后给用户。
"""

import argparse
import base64
import json
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
from engine.config_loader import config_path  # noqa: E402
from engine.model_config import language_map, style_files, MODEL_GEMINI_IMAGE  # noqa: E402
from engine.schemas.poster_models import PosterPromptOut, ReferenceStyleOut  # noqa: E402

POSTER_TOOL = "poster_tool"


class PromptBuildError(Exception):
    """组 prompt(文本管线)失败:供 _main 捕获后走降级,而非裸崩。"""


def _render(template_str: str, *, where: str, **kwargs) -> str:
    """safe_render 的薄封装。

    渲染面吃用户可控输入(user_prompt / event 字段),沙箱可能因模板语法异常而抛;
    包成 PromptBuildError 给出清晰定位,让上层降级而非裸 traceback。
    """
    try:
        return safe_render(template_str, **kwargs)
    except Exception as e:
        raise PromptBuildError(
            f"模板渲染失败({where}): {type(e).__name__}: {e}。"
            f"通常是输入里含未转义的 Jinja 语法({{{{ }}}}/{{% %}});请检查 --prompt / event 字段。"
        ) from e


# ── 组 prompt(对齐 poster_model_2,去 track_timing/DB)──────────────
async def _generate_structured_prompt(prompt: str, module: str) -> str:
    llm = get_llm_client()
    completion = await llm.generate(
        module=module, prompt=[prompt],
        response_schema=PosterPromptOut, enable_thinking=True,
    )
    r = parse_structured(completion, PosterPromptOut)
    return "\n\n".join([
        r.section_1_aesthetic, r.section_2_composition, r.section_3_visual_elements,
        r.section_4_color_palette, r.section_5_lighting_atmosphere, r.section_6_secondary_elements,
        r.section_7_text_zones, r.section_8_mood_summary, r.section_9_main_text_spec,
        r.section_10_datetime_location_spec,
    ])


async def _refine_prompt_with_theme(original_prompt, event_name, theme, module) -> str:
    prompt_data = load_yaml("system_tool.yaml")
    refine_instruction = _render(
        prompt_data["poster_theme_refine"], where="poster_theme_refine",
        event_name=event_name, theme=theme, original_prompt=original_prompt,
    )
    llm = get_llm_client()
    completion = await llm.generate(module=module, prompt=[refine_instruction], enable_thinking=True)
    return completion.text


def _build_intent_from_style(poster_style, language) -> str:
    """读 style 知识库 md(路径改为 bundle 内 engine/config/poster_tool/)。"""
    if not poster_style:
        return ""
    out = []
    lang = language_map.get(language) or "zh"
    for style in poster_style:
        fname = style_files.get(style.replace(" ", "").lower())
        if not fname:
            continue
        p = config_path("poster_tool", lang, fname)
        if p.exists():
            out.append(p.read_text(encoding="utf-8"))
    return "\n\n".join(out)


async def _analyze_reference_style(reference_image, module) -> str:
    prompt_data = load_yaml("system_tool.yaml")
    llm = get_llm_client()
    resp = await llm.generate(
        module=module, prompt=[prompt_data["reference_style_analysis"], reference_image],
        response_schema=ReferenceStyleOut,
    )
    return parse_structured(resp, ReferenceStyleOut).style_guide


def _strip_placeholder_midnight(time_start):
    """活动没给具体钟点时,抽取常把时间补成 00:00;海报别把这个假午夜印上去,只留日期。"""
    if not time_start:
        return time_start
    text = str(time_start).strip()
    for separator in (" ", "T"):
        if separator in text:
            date_part, _, time_part = text.partition(separator)
            # 00:00 / 00:00:00 全是 0 → 占位午夜,丢掉只留日期;真实钟点(如 00:30)保留
            if time_part.strip() and time_part.replace(":", "").strip("0") == "":
                return date_part.strip()
            break
    return text


async def _build_generation_prompt(*, event, host, user_prompt, language,
                                   poster_style, event_color, module, reference_image=None) -> str:
    prompt_data = load_yaml("system_tool.yaml")
    if reference_image is not None:
        intent_prompt = await _analyze_reference_style(reference_image, module)
    else:
        intent_prompt = _build_intent_from_style(poster_style, language)

    social_prompt = _render(
        prompt_data[POSTER_TOOL], where="poster_tool",
        event_name=event.get("event_name"),
        theme=event.get("theme"),
        startDate=_strip_placeholder_midnight(event.get("time_start")),
        location=event.get("location"),
        attendees=event.get("attendees"),
        prompt=user_prompt,
        language=language,
        event_color=event_color,
        organization_name=host.get("host_name"),
        has_reference=reference_image is not None,
    )
    enhanced = await _generate_structured_prompt(f"{social_prompt}\n{intent_prompt}", module)

    event_name, theme = event.get("event_name", ""), event.get("theme", "")
    if event_name or theme:
        enhanced = await _refine_prompt_with_theme(enhanced, event_name, theme, module)
    return enhanced


def _load_reference(path):
    if not path:
        return None
    try:
        from PIL import Image  # 懒加载:只有用参考图才需要 Pillow
        return Image.open(path).convert("RGB")
    except Exception as e:
        print(f"[warn] 参考图加载失败({e}),忽略参考图继续。", file=sys.stderr)
        return None


def _resolve_inputs(args) -> dict:
    data = context_local.load_json("poster_input") or {}
    styles = args.style or data.get("poster_style") or ["minimalist"]
    if isinstance(styles, str):
        styles = [styles]
    return {
        "poster_style": styles,
        "ratio": args.ratio or data.get("ratio", "1:1"),
        "resolution": args.resolution or data.get("resolution", "1K"),
        "user_prompt": args.prompt or data.get("prompt", ""),
        "event_color": args.color or data.get("event_color"),
        "reference_image_path": args.reference or data.get("reference_image"),
    }


async def _main() -> int:
    p = argparse.ArgumentParser(description="生成活动海报图")
    p.add_argument("--style", action="append", help="风格(可多次);见 SKILL.md 风格清单")
    p.add_argument("--ratio", help="比例,如 1:1 / 9:16 / 16:9")
    p.add_argument("--resolution", help="分辨率,如 1K / 2K / 4K")
    p.add_argument("--prompt", help="额外的用户方向描述")
    p.add_argument("--color", help="主色,如 #1a1a2e")
    p.add_argument("--reference", help="参考图本地路径(可选,需 Pillow)")
    args = p.parse_args()

    event = context_local.load_json("event", required=True)
    host = context_local.load_json("host", required=True)
    inp = _resolve_inputs(args)
    language = event.get("language", "中文")
    module = f"poster_tool_{'_'.join(inp['poster_style'])}_{inp['resolution']}"
    reference_image = _load_reference(inp["reference_image_path"])

    notes = []

    # 1) 组 prompt(任何文本档 Key 都能跑)。模板渲染 / 结构化解析失败时降级:
    #    不裸崩,产出一个标注 degraded 的结果,把原因计入 notes。
    try:
        generation_prompt = await _build_generation_prompt(
            event=event, host=host, user_prompt=inp["user_prompt"], language=language,
            poster_style=inp["poster_style"], event_color=inp["event_color"],
            module=module, reference_image=reference_image,
        )
    except (PromptBuildError, RuntimeError) as e:
        # PromptBuildError: safe_render 渲染失败(用户可控输入);
        # RuntimeError: parse_structured 对截断/非法结构化输出的清晰异常。
        result = {
            "ok": False,
            "workdir": str(context_local.workdir()),
            "style": inp["poster_style"], "ratio": inp["ratio"], "resolution": inp["resolution"],
            "generation_poster_prompt": None,
            "image": None,
            "notes": [
                {"stage": "build_prompt", "degraded": True,
                 "reason": f"{type(e).__name__}: {e}",
                 "hint": "组 prompt(文本管线)失败,未生成 generation_prompt;"
                         "检查 --prompt / event 字段是否含非法 Jinja 语法,或 LLM 结构化输出是否被截断后重试。"},
            ],
        }
        context_local.save_json("poster", result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    result = {
        "ok": True,
        "workdir": str(context_local.workdir()),
        "style": inp["poster_style"], "ratio": inp["ratio"], "resolution": inp["resolution"],
        "generation_poster_prompt": generation_prompt,
        "image": None,
        "notes": notes,
    }

    # 2) 生成图像(需计费档 Key;失败则降级,但 prompt 已产出)
    try:
        prompt_content = [generation_prompt] + ([reference_image] if reference_image is not None else [])
        llm = get_llm_client()
        image_response = await llm.generate_image(
            module=module, prompt=prompt_content,
            aspect_ratio=inp["ratio"], image_size=inp["resolution"],
        )
        # 找一个未占用的文件名
        n = 1
        while (context_local.workdir() / f"poster_{n}.png").exists():
            n += 1
        out_png = context_local.workdir() / f"poster_{n}.png"
        out_png.write_bytes(image_response.image_bytes)
        result["image"] = {
            "saved_to": str(out_png),
            "base64_len": len(base64.b64encode(image_response.image_bytes)),
            "mime": image_response.mime_type,
        }
    except Exception as e:
        result["image"] = {
            "degraded": True,
            "reason": f"{type(e).__name__}: {e}",
            "hint": f"图像生成需计费档 Key(模型 {MODEL_GEMINI_IMAGE})。"
                    f"免费档无图像权限时此步跳过,但 generation_prompt 已生成。先跑 python engine/doctor.py 探权限。",
        }

    context_local.save_json("poster", result)
    context_local.merge_into("plan", {"poster": {"prompt": generation_prompt, "image": result["image"]}})
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_skill_main(_main))
