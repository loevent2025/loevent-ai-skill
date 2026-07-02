"""读环境变量,决定文本供应商配置。

返回 None = 没配多供应商 → 调用方走现状 Gemini 默认路径(向后兼容)。
配置来源(任选其一):
  - LOEVENT_TEXT_PROVIDER=glm 选内置 preset(base_url/档位自动带出),再配 LOEVENT_TEXT_MODEL + LOEVENT_TEXT_API_KEY;
  - LOEVENT_TEXT_BASE_URL=... 自定义任意 OpenAI 兼容端点(直连厂商或网关 OneAPI/OpenRouter)。
"""
import os
import logging
from dataclasses import dataclass
from typing import Optional

from .presets import TEXT_PRESETS, IMAGE_PRESETS, IMAGE_EDIT_PRESETS

logger = logging.getLogger(__name__)

_warned_unsupported = set()   # 进程内每个理论兼容 provider 只提示一次,避免一个 skill 多次调用刷屏


@dataclass(frozen=True)
class TextProviderConfig:
    name: str
    base_url: str
    model: str
    api_key: str
    structured_tier: str
    needs_json_keyword: bool
    native_search: str
    supported: bool          # True=官方实测背书(Gemini/GLM);False=理论兼容,自行验证


def resolve_text_provider() -> Optional[TextProviderConfig]:
    name = os.environ.get("LOEVENT_TEXT_PROVIDER", "").strip().lower()
    base_url = os.environ.get("LOEVENT_TEXT_BASE_URL", "").strip()
    model = os.environ.get("LOEVENT_TEXT_MODEL", "").strip()
    api_key = os.environ.get("LOEVENT_TEXT_API_KEY", "").strip()

    if not name and not base_url:
        return None                          # 没配 → Gemini 默认
    if name in ("gemini", "google"):
        return None                          # 显式选 Gemini → 仍走原生 google-genai

    preset = TEXT_PRESETS.get(name) if name else None
    if name and preset is None and not base_url:
        raise RuntimeError(
            f"未知文本供应商 '{name}'。可选 preset:{', '.join(sorted(TEXT_PRESETS))};"
            "或用 LOEVENT_TEXT_BASE_URL 自定义(直连厂商或网关)。"
        )

    tier = os.environ.get("LOEVENT_TEXT_STRUCTURED_TIER", "").strip().lower()
    if base_url:                             # 自定义 base_url(可叠 preset 带出的档位)
        tier = tier or (preset.structured_tier if preset else "json_object")
        needs_keyword = preset.needs_json_keyword if preset else False
        native_search = preset.native_search if preset else ""
        supported = False                    # 自定义端点一律视为未实测,自行验证
    else:                                    # 纯 preset
        base_url = preset.base_url
        tier = tier or preset.structured_tier
        needs_keyword = preset.needs_json_keyword
        native_search = preset.native_search
        supported = preset.supported

    if not model:
        raise RuntimeError(f"文本供应商 '{name or base_url}' 缺 model:请设 LOEVENT_TEXT_MODEL。")
    if not api_key:
        raise RuntimeError(f"文本供应商 '{name or base_url}' 缺 key:请设 LOEVENT_TEXT_API_KEY。")

    label = name or base_url
    if not supported and label not in _warned_unsupported:
        _warned_unsupported.add(label)
        logger.warning("文本供应商 '%s' 属「理论兼容」(OpenAI 兼容、能跑但未官方实测),请自行验证输出质量;"
                       "官方实测背书的目前是 Gemini 与 GLM。", label)

    return TextProviderConfig(
        name=name or base_url, base_url=base_url, model=model, api_key=api_key,
        structured_tier=tier, needs_json_keyword=needs_keyword, native_search=native_search,
        supported=supported,
    )


@dataclass(frozen=True)
class ImageProviderConfig:
    name: str
    base_url: str
    model: str
    api_key: str
    supported: bool


def resolve_image_provider() -> Optional[ImageProviderConfig]:
    """读 LOEVENT_IMAGE_* 决定文生图供应商;没配 / 选 gemini → None(由 Gemini 兜底)。"""
    name = os.environ.get("LOEVENT_IMAGE_PROVIDER", "").strip().lower()
    base_url = os.environ.get("LOEVENT_IMAGE_BASE_URL", "").strip()
    model = os.environ.get("LOEVENT_IMAGE_MODEL", "").strip()
    api_key = os.environ.get("LOEVENT_IMAGE_API_KEY", "").strip()

    if not name and not base_url:
        return None
    if name in ("gemini", "google"):
        return None

    preset = IMAGE_PRESETS.get(name) if name else None
    if name and preset is None and not base_url:
        raise RuntimeError(
            f"未知文生图供应商 '{name}'。可选 preset:{', '.join(sorted(IMAGE_PRESETS))};"
            "或用 LOEVENT_IMAGE_BASE_URL 自定义。"
        )
    if base_url:
        supported = False
    else:
        base_url = preset.base_url
        supported = preset.supported

    if not model:
        raise RuntimeError(f"文生图供应商 '{name or base_url}' 缺 model:请设 LOEVENT_IMAGE_MODEL。")
    if not api_key:
        raise RuntimeError(f"文生图供应商 '{name or base_url}' 缺 key:请设 LOEVENT_IMAGE_API_KEY。")

    label = name or base_url
    if not supported and ("img:" + label) not in _warned_unsupported:
        _warned_unsupported.add("img:" + label)
        logger.warning("文生图供应商 '%s' 属「理论兼容」(OpenAI 兼容、能跑但未官方实测),请自行验证;"
                       "图像侧官方背书仍是 Gemini。", label)

    return ImageProviderConfig(name=label, base_url=base_url, model=model, api_key=api_key, supported=supported)


@dataclass(frozen=True)
class ImageEditConfig:
    name: str
    base_url: str
    model: str
    api_key: str
    supported: bool


def resolve_image_edit_provider() -> Optional["ImageEditConfig"]:
    """读 LOEVENT_IMAGE_EDIT_* 决定消字/图像编辑供应商;没配 / 选 gemini → None(由 Gemini 兜底;无图像 API 则抹字不可用)。"""
    name = os.environ.get("LOEVENT_IMAGE_EDIT_PROVIDER", "").strip().lower()
    base_url = os.environ.get("LOEVENT_IMAGE_EDIT_BASE_URL", "").strip()
    model = os.environ.get("LOEVENT_IMAGE_EDIT_MODEL", "").strip()
    api_key = os.environ.get("LOEVENT_IMAGE_EDIT_API_KEY", "").strip()

    if not name and not base_url:
        return None
    if name in ("gemini", "google"):
        return None

    preset = IMAGE_EDIT_PRESETS.get(name) if name else None
    if name and preset is None and not base_url:
        raise RuntimeError(
            f"未知图像编辑供应商 '{name}'。可选 preset:{', '.join(sorted(IMAGE_EDIT_PRESETS))};"
            "或用 LOEVENT_IMAGE_EDIT_BASE_URL 自定义。"
        )
    if base_url:
        supported = False
    else:
        base_url = preset.base_url
        supported = preset.supported

    if not model:
        raise RuntimeError(f"图像编辑供应商 '{name or base_url}' 缺 model:请设 LOEVENT_IMAGE_EDIT_MODEL(如 qwen-image-edit)。")
    if not api_key:
        raise RuntimeError(f"图像编辑供应商 '{name or base_url}' 缺 key:请设 LOEVENT_IMAGE_EDIT_API_KEY。")

    label = name or base_url
    if not supported and ("imgedit:" + label) not in _warned_unsupported:
        _warned_unsupported.add("imgedit:" + label)
        logger.warning("图像编辑供应商 '%s' 属「理论兼容」(真机未验证),请自行验证消字效果;"
                       "图像编辑侧官方背书仍是 Gemini。", label)

    return ImageEditConfig(name=label, base_url=base_url, model=model, api_key=api_key, supported=supported)
