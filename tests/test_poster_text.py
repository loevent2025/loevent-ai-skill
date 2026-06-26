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
