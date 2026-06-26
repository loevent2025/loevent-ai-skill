"""timeline 倒排期缩放数学(calculate_actual_duration 是时间线的核心计算)。"""

import pytest


def test_factors_are_one_when_prep_equals_baseline(load_script):
    timeline = load_script("skill-timeline/scripts/run.py")
    factors = timeline.calculate_actual_duration(10, "2026-01-01", "2026-01-11")  # 正好 10 天
    assert set(factors) == {"General", "Commercial", "Venue", "Marketing"}
    for value in factors.values():
        assert abs(value - 1.0) < 1e-9
    # General/Venue 同系数(gv),Commercial/Marketing 同系数(mc)
    assert factors["General"] == factors["Venue"]
    assert factors["Commercial"] == factors["Marketing"]


def test_raises_when_end_not_after_start(load_script):
    timeline = load_script("skill-timeline/scripts/run.py")
    with pytest.raises(ValueError):
        timeline.calculate_actual_duration(10, "2026-01-11", "2026-01-01")  # 活动日早于筹备日
    with pytest.raises(ValueError):
        timeline.calculate_actual_duration(10, "2026-01-01", "2026-01-01")  # prep_days = 0


def test_longer_prep_scales_up(load_script):
    timeline = load_script("skill-timeline/scripts/run.py")
    factors = timeline.calculate_actual_duration(10, "2026-01-01", "2026-02-01")  # 31 天 > 基准
    assert factors["General"] > 1.0
    assert factors["Commercial"] > 1.0
