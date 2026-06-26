"""数据完整性:知识库/数据被改坏时,这些测试比线上跑更早发现。"""

import json
from pathlib import Path

from engine.model_config import style_files

REPO_ROOT = Path(__file__).resolve().parent.parent


def _walk_low_high(obj):
    """递归找出所有同时含 low/high 的 dict(不管嵌多深)。"""
    found = []
    if isinstance(obj, dict):
        if "low" in obj and "high" in obj:
            found.append(obj)
        for value in obj.values():
            found += _walk_low_high(value)
    elif isinstance(obj, list):
        for value in obj:
            found += _walk_low_high(value)
    return found


def test_budget_low_not_greater_than_high():
    budget_files = sorted((REPO_ROOT / "engine/config/budget").glob("*.json"))
    assert budget_files, "没找到任何 budget 价库 JSON"
    for budget_file in budget_files:
        data = json.loads(budget_file.read_text(encoding="utf-8"))
        pairs = _walk_low_high(data)
        assert pairs, f"{budget_file.name} 里没有任何 low/high 项"
        for pair in pairs:
            low, high = pair["low"], pair["high"]
            if isinstance(low, (int, float)) and isinstance(high, (int, float)):
                assert low <= high, f"{budget_file.name}: low({low}) > high({high})"


def test_poster_style_files_exist():
    style_dir = REPO_ROOT / "engine/config/poster_tool/zh"
    assert style_files, "style_files 映射为空"
    for filename in style_files.values():
        assert (style_dir / filename).exists(), f"缺海报风格文件: {filename}"
