"""文本供应商 preset 注册表:每家一行(base_url + 结构化档位 + 兼容位)。

加一家新供应商 = 加一行;用户也可用 LOEVENT_TEXT_BASE_URL 自定义覆盖(直连厂商或网关)。
model 一律由用户用 LOEVENT_TEXT_MODEL 指定(模型名更新快,不在代码里写死会过期的默认值)。

structured_tier(结构化输出档位,决定怎么要 JSON):
  json_schema —— 服务端受约束解码(GLM/Kimi/OpenAI),最稳;
  json_object —— 只保证合法 JSON(Qwen/ERNIE/DeepSeek/豆包/MiniMax),靠 Pydantic 校验兜底。
native_search —— 该家原生联网搜索的开启方式(P2 才用;空 = 无原生搜索,需走外部搜索)。
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class TextProviderPreset:
    base_url: str
    structured_tier: str = "json_object"
    needs_json_keyword: bool = False   # json_object 模式是否要求 prompt 里出现 "json"
    native_search: str = ""
    supported: bool = False            # True=官方实测背书;False=理论兼容(能跑但未实测,用户自行验证)


TEXT_PRESETS = {
    "glm": TextProviderPreset(
        base_url="https://open.bigmodel.cn/api/paas/v4/",
        structured_tier="json_schema",
        native_search="web_search_tool",
        supported=True,            # 官方支持(连同现状 Gemini);其余各家为"理论兼容",实测后再逐一升级
    ),
    "kimi": TextProviderPreset(
        base_url="https://api.moonshot.cn/v1",
        structured_tier="json_schema",
        native_search="builtin_web_search",
    ),
    "deepseek": TextProviderPreset(
        base_url="https://api.deepseek.com",
        structured_tier="json_object",
        native_search="",   # 标准端点无原生搜索 → 强制走外部搜索(P2)
    ),
    "qwen": TextProviderPreset(
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        structured_tier="json_object",
        needs_json_keyword=True,
        native_search="enable_search",
    ),
    "ernie": TextProviderPreset(
        base_url="https://qianfan.baidubce.com/v2",
        structured_tier="json_object",
        needs_json_keyword=True,
        native_search="web_search_top",
    ),
    "doubao": TextProviderPreset(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        structured_tier="json_object",
        native_search="web_search_plugin",
    ),
    "minimax": TextProviderPreset(
        base_url="https://api.minimaxi.com/v1",
        structured_tier="json_object",
    ),
    "openai": TextProviderPreset(
        base_url="https://api.openai.com/v1",
        structured_tier="json_schema",
    ),
}


@dataclass(frozen=True)
class ImageProviderPreset:
    """文生图 preset(P3:OpenAI 兼容 /images/generations 同步家)。

    都返回图片 URL(豆包也支持 b64),用 openai SDK images.generate 调、再下载成 bytes。
    supported 一律 False:图像侧官方实测背书仍是现状 Gemini,这些是理论兼容、自行验证。
    异步轮询家(万相/可图)与编辑/消字(qwen-image-edit/iRAG)留作 P3.5。
    """
    base_url: str
    supported: bool = False


IMAGE_PRESETS = {
    "doubao": ImageProviderPreset(base_url="https://ark.cn-beijing.volces.com/api/v3"),
    "cogview": ImageProviderPreset(base_url="https://open.bigmodel.cn/api/paas/v4/"),
    "openai": ImageProviderPreset(base_url="https://api.openai.com/v1"),
}


@dataclass(frozen=True)
class ImageEditPreset:
    """图像编辑/消字 preset(P3.5:指令式编辑,海报消字用)。

    qwen-image-edit 走 DashScope 多模态生成端点:同步、接受 base64 输入图、指令式编辑、返回图片 URL。
    supported 一律 False:理论兼容、真机未验证,自行验证。千帆 /v2/images/edits(URL+mask)留作后续。
    """
    base_url: str
    supported: bool = False


IMAGE_EDIT_PRESETS = {
    "qwen": ImageEditPreset(
        base_url="https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
    ),
}
