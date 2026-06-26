"""多供应商文本/搜索/图像层的确定性逻辑(全部无需 key)。"""
import asyncio
import base64
import logging
import pytest

from engine.providers import MultiProviderClient
from engine.providers.presets import TEXT_PRESETS
from engine.providers.config import resolve_text_provider, resolve_image_provider, TextProviderConfig
from engine.providers.openai_compat import OpenAICompatClient, _strip_fence
from engine.providers.image_openai import OpenAICompatImageProvider
from engine.providers.grounding import resolve_grounding_provider, BochaSearch, TavilySearch
from engine.schemas.timeline_models import TimelineOutput

_ENV_KEYS = ("LOEVENT_TEXT_PROVIDER", "LOEVENT_TEXT_BASE_URL", "LOEVENT_TEXT_MODEL",
             "LOEVENT_TEXT_API_KEY", "LOEVENT_TEXT_STRUCTURED_TIER",
             "LOEVENT_SEARCH_PROVIDER", "LOEVENT_SEARCH_API_KEY", "LOEVENT_ALLOW_UNGROUNDED",
             "LOEVENT_IMAGE_PROVIDER", "LOEVENT_IMAGE_BASE_URL", "LOEVENT_IMAGE_MODEL",
             "LOEVENT_IMAGE_API_KEY", "LOEVENT_IMAGE_SIZE",
             "LOEVENT_IMAGE_EDIT_PROVIDER", "LOEVENT_IMAGE_EDIT_BASE_URL",
             "LOEVENT_IMAGE_EDIT_MODEL", "LOEVENT_IMAGE_EDIT_API_KEY",
             "LOEVENT_OCR_PROVIDER", "LOEVENT_OCR_BASE_URL",
             "LOEVENT_OCR_MODEL", "LOEVENT_OCR_API_KEY")


class _FakeResp:
    """假的 OpenAI ChatCompletion 响应,用于无 key 测 content/finish_reason/usage 提取与重试。"""
    def __init__(self, content, finish_reason="stop", completion_tokens=10):
        message = type("_Msg", (), {"content": content})()
        choice = type("_Choice", (), {"message": message, "finish_reason": finish_reason})()
        self.choices = [choice]
        self.usage = type("_Usage", (), {"completion_tokens": completion_tokens})()


def _clear_env(monkeypatch):
    for k in _ENV_KEYS:
        monkeypatch.delenv(k, raising=False)


# ── presets ──
def test_glm_preset_is_json_schema_tier():
    glm = TEXT_PRESETS["glm"]
    assert glm.base_url == "https://open.bigmodel.cn/api/paas/v4/"
    assert glm.structured_tier == "json_schema"


def test_qwen_needs_json_keyword():
    assert TEXT_PRESETS["qwen"].needs_json_keyword is True
    assert TEXT_PRESETS["qwen"].structured_tier == "json_object"


# ── config 解析 ──
def test_no_config_returns_none(monkeypatch):
    _clear_env(monkeypatch)
    assert resolve_text_provider() is None


def test_gemini_explicit_returns_none(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("LOEVENT_TEXT_PROVIDER", "gemini")
    assert resolve_text_provider() is None


def test_glm_preset_resolves(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("LOEVENT_TEXT_PROVIDER", "glm")
    monkeypatch.setenv("LOEVENT_TEXT_MODEL", "glm-4.6")
    monkeypatch.setenv("LOEVENT_TEXT_API_KEY", "test-key")
    cfg = resolve_text_provider()
    assert cfg.base_url == "https://open.bigmodel.cn/api/paas/v4/"
    assert cfg.structured_tier == "json_schema"
    assert cfg.model == "glm-4.6"
    assert cfg.supported is True            # GLM 官方支持


def test_unsupported_preset_flagged(monkeypatch):
    # 理论兼容的家(如 qwen)→ supported False(运行时会提示"自行验证")
    _clear_env(monkeypatch)
    monkeypatch.setenv("LOEVENT_TEXT_PROVIDER", "qwen")
    monkeypatch.setenv("LOEVENT_TEXT_MODEL", "qwen-plus")
    monkeypatch.setenv("LOEVENT_TEXT_API_KEY", "k")
    assert resolve_text_provider().supported is False


def test_custom_base_url_unsupported(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("LOEVENT_TEXT_BASE_URL", "http://localhost:3000/v1")
    monkeypatch.setenv("LOEVENT_TEXT_MODEL", "x")
    monkeypatch.setenv("LOEVENT_TEXT_API_KEY", "k")
    assert resolve_text_provider().supported is False   # 自定义端点一律未实测


def test_unknown_preset_raises(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("LOEVENT_TEXT_PROVIDER", "nope")
    monkeypatch.setenv("LOEVENT_TEXT_MODEL", "x")
    monkeypatch.setenv("LOEVENT_TEXT_API_KEY", "k")
    with pytest.raises(RuntimeError):
        resolve_text_provider()


def test_missing_key_raises(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("LOEVENT_TEXT_PROVIDER", "glm")
    monkeypatch.setenv("LOEVENT_TEXT_MODEL", "glm-4.6")
    with pytest.raises(RuntimeError):
        resolve_text_provider()


def test_custom_base_url_for_gateway(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("LOEVENT_TEXT_BASE_URL", "http://localhost:3000/v1")  # OneAPI/网关
    monkeypatch.setenv("LOEVENT_TEXT_MODEL", "whatever")
    monkeypatch.setenv("LOEVENT_TEXT_API_KEY", "k")
    cfg = resolve_text_provider()
    assert cfg.base_url == "http://localhost:3000/v1"
    assert cfg.structured_tier == "json_object"  # 自定义无 preset → 默认档


# ── OpenAICompatClient 纯逻辑 ──
def _client(tier="json_schema", needs_kw=False):
    cfg = TextProviderConfig(name="t", base_url="http://x/v1", model="m", api_key="k",
                             structured_tier=tier, needs_json_keyword=needs_kw, native_search="",
                             supported=True)
    return OpenAICompatClient(cfg)


def test_request_json_schema_tier():
    req = _client("json_schema")._build_request([{"role": "user", "content": "hi"}], TimelineOutput, None)
    assert req["response_format"]["type"] == "json_schema"
    assert "schema" in req["response_format"]["json_schema"]


def test_request_json_object_tier():
    req = _client("json_object")._build_request([{"role": "user", "content": "hi"}], TimelineOutput, None)
    assert req["response_format"]["type"] == "json_object"


def test_json_object_injects_schema_hint():
    msgs = _client("json_object")._build_messages("SYS", "do it", TimelineOutput, None)
    system_text = [m for m in msgs if m["role"] == "system"][0]["content"]
    assert "json" in system_text.lower()   # 满足 needs_json_keyword 的家


def test_json_schema_does_not_pollute_prompt():
    msgs = _client("json_schema")._build_messages("SYS", "do it", TimelineOutput, None)
    system_text = [m for m in msgs if m["role"] == "system"][0]["content"]
    assert system_text == "SYS"   # json_schema 档靠 response_format,不往 prompt 塞 schema


def test_strip_fence():
    assert _strip_fence("```json\n{\"a\":1}\n```") == '{"a":1}'


def test_image_raises_p3():
    with pytest.raises(RuntimeError):
        asyncio.run(_client().generate_image(module="x", prompt="hi"))


# ── P2 grounding ──
def test_search_unconfigured_returns_none(monkeypatch):
    _clear_env(monkeypatch)
    assert resolve_grounding_provider() is None       # 没配 → None(调用方显式降级)


def test_search_none_returns_none(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("LOEVENT_SEARCH_PROVIDER", "none")
    assert resolve_grounding_provider() is None


def test_search_bocha_resolves(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("LOEVENT_SEARCH_PROVIDER", "bocha")
    monkeypatch.setenv("LOEVENT_SEARCH_API_KEY", "k")
    assert isinstance(resolve_grounding_provider(), BochaSearch)


def test_search_missing_key_raises(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("LOEVENT_SEARCH_PROVIDER", "tavily")
    with pytest.raises(RuntimeError):
        resolve_grounding_provider()


def test_bocha_parse_nested():
    data = {"data": {"webPages": {"value": [
        {"name": "标题A", "url": "http://a", "summary": "摘要A", "datePublished": "2026-06-01"},
    ]}}}
    out = BochaSearch._parse(data)
    assert len(out) == 1 and out[0].title == "标题A" and out[0].url == "http://a" and out[0].snippet == "摘要A"


def test_tavily_parse():
    out = TavilySearch._parse({"results": [{"title": "T", "url": "http://t", "content": "正文"}]})
    assert len(out) == 1 and out[0].snippet == "正文"


def test_grounding_strict_raises_when_unconfigured(monkeypatch):
    # H2:默认严格——没配外部搜索 → 报错(让 skill 走降级,不静默编造)
    _clear_env(monkeypatch)
    with pytest.raises(RuntimeError):
        asyncio.run(_client()._apply_grounding("find trends", module="x"))


def test_grounding_allow_ungrounded_returns_none(monkeypatch):
    # 显式放行 → 原样 prompt + 'none'
    _clear_env(monkeypatch)
    monkeypatch.setenv("LOEVENT_ALLOW_UNGROUNDED", "1")
    new_prompt, source = asyncio.run(_client()._apply_grounding("find trends", module="x"))
    assert source == "none" and new_prompt == "find trends"


def test_grounding_happy_path_injects(monkeypatch):
    # M2:正路径——有结果 → 注入 prompt + 返回 grounding.name
    from engine.providers.grounding import SearchResult
    client = _client()

    class _FakeSearch:
        name = "fake"
        async def search(self, query, top_k=8):
            return [SearchResult("标题", "http://x", "摘要", "2026-06")]

    monkeypatch.setattr("engine.providers.grounding.resolve_grounding_provider", lambda: _FakeSearch())

    async def _fake_propose(prompt, module):
        return ["q1"]
    monkeypatch.setattr(client, "_propose_queries", _fake_propose)

    new_prompt, source = asyncio.run(client._apply_grounding("研究X", module="x"))
    assert source == "fake"
    assert "http://x" in new_prompt and "研究X" in new_prompt


def test_inject_results_carries_sources():
    from engine.providers.grounding import SearchResult
    merged = OpenAICompatClient._inject_results("原任务", [SearchResult("标题", "http://x", "摘要", "2026-06")])
    assert "http://x" in merged and "原任务" in merged and "标注来源" in merged


# ── 审查修复回归 ──
def test_unsupported_warning_dedups(monkeypatch, caplog):
    # ① 理论兼容的家:多次 resolve 只警告一次(避免一个 skill 多次调用刷屏)
    from engine.providers import config as config_module
    config_module._warned_unsupported.clear()
    _clear_env(monkeypatch)
    monkeypatch.setenv("LOEVENT_TEXT_PROVIDER", "qwen")
    monkeypatch.setenv("LOEVENT_TEXT_MODEL", "qwen-plus")
    monkeypatch.setenv("LOEVENT_TEXT_API_KEY", "k")
    with caplog.at_level(logging.WARNING):
        resolve_text_provider()
        resolve_text_provider()
        resolve_text_provider()
    warns = [r for r in caplog.records if "理论兼容" in r.getMessage()]
    assert len(warns) == 1


def test_grounding_empty_raises_by_default(monkeypatch):
    # H2:配了搜索但搜空 → 默认严格报错(不静默降级编造)
    client = _client()

    class _FakeEmptySearch:
        name = "fake"
        async def search(self, query, top_k=8):
            return []

    monkeypatch.setattr("engine.providers.grounding.resolve_grounding_provider", lambda: _FakeEmptySearch())

    async def _fake_propose(prompt, module):
        return ["q1"]
    monkeypatch.setattr(client, "_propose_queries", _fake_propose)
    monkeypatch.delenv("LOEVENT_ALLOW_UNGROUNDED", raising=False)

    with pytest.raises(RuntimeError):
        asyncio.run(client._apply_grounding("task", module="x"))


# ── P3 图像 ──
def test_image_unconfigured_returns_none(monkeypatch):
    _clear_env(monkeypatch)
    assert resolve_image_provider() is None


def test_image_gemini_returns_none(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("LOEVENT_IMAGE_PROVIDER", "gemini")
    assert resolve_image_provider() is None       # 显式 Gemini → 仍走原生 Gemini 出图


def test_image_doubao_resolves(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("LOEVENT_IMAGE_PROVIDER", "doubao")
    monkeypatch.setenv("LOEVENT_IMAGE_MODEL", "doubao-seedream-4-0")
    monkeypatch.setenv("LOEVENT_IMAGE_API_KEY", "k")
    cfg = resolve_image_provider()
    assert cfg.base_url == "https://ark.cn-beijing.volces.com/api/v3"
    assert cfg.supported is False                 # 图像侧官方背书仍是 Gemini


def test_image_missing_key_raises(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("LOEVENT_IMAGE_PROVIDER", "cogview")
    monkeypatch.setenv("LOEVENT_IMAGE_MODEL", "cogview-4")
    with pytest.raises(RuntimeError):
        resolve_image_provider()


def test_image_extract_b64():
    class _Item:
        b64_json = base64.b64encode(b"PNGDATA").decode()
        url = None
    out = asyncio.run(OpenAICompatImageProvider._extract_bytes(_Item()))
    assert out == b"PNGDATA"


def test_image_size_default_none(monkeypatch):
    monkeypatch.delenv("LOEVENT_IMAGE_SIZE", raising=False)
    assert OpenAICompatImageProvider._resolve_size("1K", "1:1") is None


def test_image_size_env_override(monkeypatch):
    monkeypatch.setenv("LOEVENT_IMAGE_SIZE", "1024x1536")
    assert OpenAICompatImageProvider._resolve_size("1K", "3:4") == "1024x1536"


def test_image_routing_text_prompt_uses_t2i():
    class _FakeT2I:
        async def generate_image(self, **kw):
            return "t2i-img"

    class _FakeGemini:
        async def generate_image(self, **kw):
            return "gemini-img"

    mpc = MultiProviderClient(text_client=None, image_t2i=_FakeT2I(), image_fallback=_FakeGemini())
    assert asyncio.run(mpc.generate_image(module="x", prompt="一张海报")) == "t2i-img"


def test_image_routing_image_prompt_uses_gemini_fallback():
    # 带图 prompt(编辑/消字,非 str)→ 走 Gemini 兜底,不走文生图 t2i
    class _FakeGemini:
        async def generate_image(self, **kw):
            return "gemini-img"

    mpc = MultiProviderClient(text_client=None, image_t2i=object(), image_fallback=_FakeGemini())
    assert asyncio.run(mpc.generate_image(module="x", prompt=[b"img", "erase"])) == "gemini-img"


def test_image_no_provider_raises():
    mpc = MultiProviderClient(text_client=None, image_t2i=None, image_fallback=None)
    with pytest.raises(RuntimeError):
        asyncio.run(mpc.generate_image(module="x", prompt="海报"))


# ── 第二轮审查修复回归(H1/H4/M1/M3)──
def test_prompt_to_text_joins_list():
    # H1:list[str] 用空行拼接,不 json.dumps 成字面量
    from engine.providers.openai_compat import _prompt_to_text
    assert _prompt_to_text(["a", "b"]) == "a\n\nb"
    assert _prompt_to_text("solo") == "solo"


def test_prompt_to_text_rejects_multimodal():
    # H1:含非 str(图像/bytes)→ 清晰报错,不抛裸 TypeError
    from engine.providers.openai_compat import _prompt_to_text
    with pytest.raises(RuntimeError):
        _prompt_to_text(["text", object()])


def test_build_messages_list_not_jsondumped():
    # H1:_build_messages 对 [str] 拼成纯文本,而非 '["..."]'
    user = [m for m in _client("json_schema")._build_messages(None, ["海报描述"], None, None)
            if m["role"] == "user"][0]["content"]
    assert user == "海报描述"


def test_image_routing_list_of_str_uses_t2i():
    # H4 关键回归:skill-poster 恒传 [generation_prompt](list of str)→ 必须走文生图供应商,不被绕过
    class _FakeT2I:
        async def generate_image(self, **kw):
            return "t2i"

    class _FakeGemini:
        async def generate_image(self, **kw):
            return "gemini"

    mpc = MultiProviderClient(text_client=None, image_t2i=_FakeT2I(), image_fallback=_FakeGemini())
    assert asyncio.run(mpc.generate_image(module="x", prompt=["海报描述"])) == "t2i"


def test_image_routing_list_with_image_uses_gemini():
    # 含图对象 → 编辑/消字 → 走 Gemini 兜底
    class _FakeGemini:
        async def generate_image(self, **kw):
            return "gemini"

    mpc = MultiProviderClient(text_client=None, image_t2i=object(), image_fallback=_FakeGemini())
    assert asyncio.run(mpc.generate_image(module="x", prompt=["描述", object()])) == "gemini"


def test_finish_reason_maps_length_to_max_tokens():
    # M1:OpenAI 'length' → 'MAX_TOKENS'(复用 runtime 截断判断)
    assert OpenAICompatClient._finish_reason_of(_FakeResp("x", finish_reason="length")) == "MAX_TOKENS"
    assert OpenAICompatClient._finish_reason_of(_FakeResp("x", finish_reason="stop")) == "STOP"


def test_output_tokens_extracted():
    assert OpenAICompatClient._output_tokens_of(_FakeResp("x", completion_tokens=42)) == 42


def test_content_of_empty_safe():
    assert OpenAICompatClient._content_of(_FakeResp(None)) == ""


def test_generate_sets_grounding_source_and_finish_reason(monkeypatch):
    # M1+M2:grounding 正路径端到端 + LLMResponse 回填
    from engine.providers.grounding import SearchResult
    client = _client()

    class _FakeSearch:
        name = "bocha"
        async def search(self, query, top_k=8):
            return [SearchResult("t", "http://u", "s", "")]

    monkeypatch.setattr("engine.providers.grounding.resolve_grounding_provider", lambda: _FakeSearch())

    async def _fake_propose(prompt, module):
        return ["q1"]
    monkeypatch.setattr(client, "_propose_queries", _fake_propose)

    captured = {}

    async def _fake_call(request, module):
        captured["messages"] = request["messages"]
        return _FakeResp("综述答案", finish_reason="length", completion_tokens=7)
    monkeypatch.setattr(client, "_call", _fake_call)

    resp = asyncio.run(client.generate(module="x", prompt="研究X", use_google_search=True))
    assert resp.used_google_search is True and resp.grounding_source == "bocha"
    assert resp.finish_reason == "MAX_TOKENS" and resp.output_tokens == 7
    assert any(isinstance(m.get("content"), str) and "http://u" in m["content"] for m in captured["messages"])


def test_validation_retries_once_then_accepts(monkeypatch):
    # M3:json_object 档兜底——首次非法 JSON → 重试一次 → 第二次合法
    from pydantic import BaseModel

    class _Tiny(BaseModel):
        x: int

    client = _client("json_schema")
    calls = {"n": 0}

    async def _fake_call(request, module):
        calls["n"] += 1
        return _FakeResp("not json" if calls["n"] == 1 else '{"x": 1}')
    monkeypatch.setattr(client, "_call", _fake_call)

    resp = asyncio.run(client.generate(module="x", prompt="hi", response_schema=_Tiny))
    assert calls["n"] == 2 and resp.text == '{"x": 1}'


def test_no_retry_when_first_valid(monkeypatch):
    from pydantic import BaseModel

    class _Tiny(BaseModel):
        x: int

    client = _client("json_schema")
    calls = {"n": 0}

    async def _fake_call(request, module):
        calls["n"] += 1
        return _FakeResp('{"x": 1}')
    monkeypatch.setattr(client, "_call", _fake_call)

    asyncio.run(client.generate(module="x", prompt="hi", response_schema=_Tiny))
    assert calls["n"] == 1


# ── P3.5 图像编辑 / 消字 ──
def test_image_edit_unconfigured_returns_none(monkeypatch):
    from engine.providers.config import resolve_image_edit_provider
    _clear_env(monkeypatch)
    assert resolve_image_edit_provider() is None


def test_image_edit_qwen_resolves(monkeypatch):
    from engine.providers.config import resolve_image_edit_provider
    _clear_env(monkeypatch)
    monkeypatch.setenv("LOEVENT_IMAGE_EDIT_PROVIDER", "qwen")
    monkeypatch.setenv("LOEVENT_IMAGE_EDIT_MODEL", "qwen-image-edit")
    monkeypatch.setenv("LOEVENT_IMAGE_EDIT_API_KEY", "k")
    cfg = resolve_image_edit_provider()
    assert "dashscope" in cfg.base_url and cfg.model == "qwen-image-edit" and cfg.supported is False


def test_image_edit_missing_key_raises(monkeypatch):
    from engine.providers.config import resolve_image_edit_provider
    _clear_env(monkeypatch)
    monkeypatch.setenv("LOEVENT_IMAGE_EDIT_PROVIDER", "qwen")
    monkeypatch.setenv("LOEVENT_IMAGE_EDIT_MODEL", "qwen-image-edit")
    with pytest.raises(RuntimeError):
        resolve_image_edit_provider()


def test_split_edit_prompt():
    from engine.providers.image_edit import _split_edit_prompt
    instruction, image = _split_edit_prompt(["抹掉文字", b"imgbytes"])
    assert instruction == "抹掉文字" and image == b"imgbytes"


def test_split_edit_prompt_no_image_raises():
    from engine.providers.image_edit import _split_edit_prompt
    with pytest.raises(RuntimeError):
        _split_edit_prompt(["只有文字"])


def test_image_to_data_uri_from_bytes():
    from engine.providers.image_edit import _image_to_data_uri
    uri = _image_to_data_uri(b"PNGDATA")
    assert uri.startswith("data:image/png;base64,") and base64.b64decode(uri.split(",", 1)[1]) == b"PNGDATA"


def test_dashscope_extract_image_url():
    from engine.providers.image_edit import DashScopeImageEditProvider
    data = {"output": {"choices": [{"message": {"content": [{"image": "http://result/x.png"}]}}]}}
    assert DashScopeImageEditProvider._extract_image_url(data) == "http://result/x.png"


def test_image_edit_routing_uses_edit_provider():
    # P3.5 关键回归:含图 prompt(消字)+ 配了消字 provider → 走它,不退 Gemini
    class _FakeEdit:
        async def generate_image(self, **kw):
            return "edited"

    class _FakeGemini:
        async def generate_image(self, **kw):
            return "gemini"

    mpc = MultiProviderClient(text_client=None, image_t2i=None,
                              image_fallback=_FakeGemini(), image_edit=_FakeEdit())
    assert asyncio.run(mpc.generate_image(module="x", prompt=["抹掉文字", b"img"])) == "edited"


def test_image_edit_falls_back_to_gemini_when_unconfigured():
    # 没配消字 provider → 含图 prompt 退 Gemini 兜底
    class _FakeGemini:
        async def generate_image(self, **kw):
            return "gemini"

    mpc = MultiProviderClient(text_client=None, image_t2i=None,
                              image_fallback=_FakeGemini(), image_edit=None)
    assert asyncio.run(mpc.generate_image(module="x", prompt=["抹掉文字", b"img"])) == "gemini"


# ── P3.6 OCR / 文字定位多供应商 ──
def test_ocr_unconfigured_returns_none(monkeypatch):
    from engine.providers.ocr import resolve_ocr_provider
    _clear_env(monkeypatch)
    assert resolve_ocr_provider() is None


def test_ocr_gcv_returns_none(monkeypatch):
    from engine.providers.ocr import resolve_ocr_provider
    _clear_env(monkeypatch)
    monkeypatch.setenv("LOEVENT_OCR_PROVIDER", "gcv")
    assert resolve_ocr_provider() is None           # 显式 GCV → poster_text 走原 GCV


def test_ocr_qwen_vl_resolves(monkeypatch):
    from engine.providers.ocr import resolve_ocr_provider, MultimodalOcrProvider
    _clear_env(monkeypatch)
    monkeypatch.setenv("LOEVENT_OCR_PROVIDER", "qwen-vl")
    monkeypatch.setenv("LOEVENT_OCR_MODEL", "qwen-vl-max")
    monkeypatch.setenv("LOEVENT_OCR_API_KEY", "k")
    provider = resolve_ocr_provider()
    assert isinstance(provider, MultimodalOcrProvider) and "dashscope" in provider._base_url


def test_ocr_missing_key_raises(monkeypatch):
    from engine.providers.ocr import resolve_ocr_provider
    _clear_env(monkeypatch)
    monkeypatch.setenv("LOEVENT_OCR_PROVIDER", "glm-4v")
    monkeypatch.setenv("LOEVENT_OCR_MODEL", "glm-4v")
    with pytest.raises(RuntimeError):
        resolve_ocr_provider()


def test_ocr_parse_clamps_boxes():
    from engine.providers.ocr import MultimodalOcrProvider
    blocks = MultimodalOcrProvider._parse('{"blocks":[{"text":"标题","box":{"x":0.1,"y":0.2,"w":1.5,"h":-0.3}}]}')
    assert blocks[0]["text"] == "标题"
    assert blocks[0]["box"]["w"] == 1.0 and blocks[0]["box"]["h"] == 0.0   # 钳到 [0,1]


def test_ocr_messages_are_multimodal():
    from engine.providers.ocr import MultimodalOcrProvider
    content = MultimodalOcrProvider("http://x", "m", "k", "t")._build_messages("data:image/png;base64,AAA")[0]["content"]
    assert any(c["type"] == "image_url" for c in content) and any(c["type"] == "text" for c in content)
