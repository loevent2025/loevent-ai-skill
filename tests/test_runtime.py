"""runtime 结构化输出健壮解析(文档点名的"解析容错")。"""

import types

import pytest

from engine.runtime import parse_structured, _strip_json_fence


def _resp(text, finish_reason=None):
    return types.SimpleNamespace(text=text, finish_reason=finish_reason)


def test_strip_json_fence():
    assert _strip_json_fence('```json\n{"a":1}\n```') == '{"a":1}'
    assert _strip_json_fence('前言 {"a":1} 后语') == '{"a":1}'
    assert _strip_json_fence('{"a":1}') == '{"a":1}'


def test_parse_plain_json():
    assert parse_structured(_resp('{"a":1}')) == {"a": 1}


def test_parse_fenced_json():
    assert parse_structured(_resp('```json\n{"a":1}\n```')) == {"a": 1}


def test_parse_json_buried_in_prose():
    # 模型偶发在 JSON 外面带话术,应能截取出 {...}
    assert parse_structured(_resp('结果如下：{"a":1,"b":2} 完毕')) == {"a": 1, "b": 2}


def test_parse_garbage_raises_clear_error():
    with pytest.raises(RuntimeError):
        parse_structured(_resp("这根本不是 JSON"))


def test_parse_truncated_gives_max_tokens_hint():
    with pytest.raises(RuntimeError, match="MAX_TOKENS"):
        parse_structured(_resp('{"a":', finish_reason="MAX_TOKENS"))
