"""poster 文字处理的确定性函数(#5 占位午夜剥离)。"""

import pytest


@pytest.mark.parametrize("time_start,expected", [
    ("2026-07-15 00:00", "2026-07-15"),       # 空格 + 午夜 → 剥
    ("2026-07-15T00:00:00", "2026-07-15"),    # ISO + 午夜 → 剥
    ("2026.07.15 00:00", "2026.07.15"),       # 点分隔 + 午夜 → 剥
    ("2026-07-15 14:30", "2026-07-15 14:30"), # 真实钟点 → 留
    ("2026-07-15 00:30", "2026-07-15 00:30"), # 00:30 是真实时间 → 留
    ("2026-07-15", "2026-07-15"),             # 只有日期 → 原样
    ("", ""),                                 # 空 → 原样
    (None, None),                             # None → 原样
])
def test_strip_placeholder_midnight(load_script, time_start, expected):
    # _strip_placeholder_midnight 在出图脚本 run.py(#5),不在 poster_text.py(#4)
    poster_run = load_script("skill-poster/scripts/run.py")
    assert poster_run._strip_placeholder_midnight(time_start) == expected


def test_ocr_agent_estimate_scaffold(load_script, monkeypatch, tmp_path):
    """GCV/VL 不可用时,build_estimate_scaffold 从 event/host 预填文字、写出 layers 模板供 agent 代劳估框。"""
    monkeypatch.setenv("LOEVENT_WORKDIR", str(tmp_path))
    from engine import context_local
    context_local.save_json("event", {"event_name": "AI 大会 2026",
                                       "time_start": "2026-09-01T19:00", "location": "上海"})
    context_local.save_json("host", {"host_name": "Acme Inc"})

    from PIL import Image
    image = tmp_path / "poster_1.png"
    Image.new("RGB", (200, 300), "purple").save(image)

    poster_text = load_script("skill-poster/scripts/poster_text.py")
    scaffold = poster_text.build_estimate_scaffold(image)

    assert scaffold["mode"] == "agent_estimate"
    assert scaffold["image_size"] == [200, 300]
    # 已知上墙文字从 event/host 预填(标题/日期/地点/主办方)
    assert "AI 大会 2026" in scaffold["known_texts"]
    assert "上海" in scaffold["known_texts"]
    assert "Acme Inc" in scaffold["known_texts"]
    assert len(scaffold["template"]["layers"]) == 4
    # 模板已写进工作目录,供 agent 就地改 + render 读
    assert (tmp_path / "poster_text_layers.json").exists()
    # 每层是 render 能吃的 schema
    layer0 = scaffold["template"]["layers"][0]
    assert set(layer0) >= {"text", "x", "y", "font_scale", "color", "align"}
