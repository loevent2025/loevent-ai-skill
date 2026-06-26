"""llm_client 的确定性逻辑:瞬时错误判定 + 文本 config 的工具接线(都不需要 key)。"""

from engine.llm_client import _is_transient, GeminiSingleKeyClient


def _config(**override):
    base = dict(system_prompt=None, response_schema=None, use_google_search=False,
                enable_url_context=False, enable_thinking=False, max_output_tokens=None)
    base.update(override)
    return GeminiSingleKeyClient._build_text_config(**base)


# ── _is_transient:瞬时连接错误才重试,逻辑错不重试 ──
def test_transient_true_for_connection_errors():
    assert _is_transient(Exception("SSL: EOF occurred in violation of protocol"))
    assert _is_transient(Exception("Connection reset by peer"))

    class ReadTimeout(Exception):
        pass
    assert _is_transient(ReadTimeout("timed out"))


def test_transient_false_for_logic_errors():
    assert not _is_transient(ValueError("invalid json"))
    assert not _is_transient(KeyError("missing field"))


# ── _build_text_config:grounding / url_context 工具接线 ──
def test_no_tools_by_default():
    assert not _config().tools


def test_google_search_tool_added():
    cfg = _config(use_google_search=True)
    assert cfg.tools and len(cfg.tools) == 1
    assert cfg.tools[0].google_search is not None


def test_url_context_and_both_tools():
    assert _config(enable_url_context=True).tools[0].url_context is not None
    assert len(_config(use_google_search=True, enable_url_context=True).tools) == 2


def test_response_schema_sets_json_mime():
    from engine.schemas.timeline_models import TimelineOutput
    cfg = _config(response_schema=TimelineOutput)
    assert cfg.response_mime_type == "application/json"
