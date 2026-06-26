"""context_local 工作目录解析 / 累加器 / 清理(确定性文件逻辑,含"别误删用户文件"的安全分支)。"""

import pytest

from engine import context_local


def test_workdir_uses_custom_env(monkeypatch, tmp_path):
    monkeypatch.setenv("LOEVENT_WORKDIR", str(tmp_path))
    assert context_local.workdir() == tmp_path.resolve()


def test_save_load_merge_roundtrip(monkeypatch, tmp_path):
    monkeypatch.setenv("LOEVENT_WORKDIR", str(tmp_path))
    context_local.save_json("plan", {"a": 1})
    assert context_local.load_json("plan") == {"a": 1}
    context_local.merge_into("plan", {"b": 2})  # 累加器:不覆盖,合并
    assert context_local.load_json("plan") == {"a": 1, "b": 2}


def test_load_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("LOEVENT_WORKDIR", str(tmp_path))
    assert context_local.load_json("nope") is None
    with pytest.raises(FileNotFoundError):
        context_local.load_json("nope", required=True)


def test_clear_custom_workdir_keeps_user_files(monkeypatch, tmp_path):
    # 自定义 workdir 模式:clear 只删 loevent 自己的产物,绝不动用户的其它文件
    monkeypatch.setenv("LOEVENT_WORKDIR", str(tmp_path))
    context_local.save_json("plan", {"a": 1})            # loevent 产物
    (tmp_path / "my_notes.txt").write_text("用户的文件")  # 无关文件
    context_local.clear_workspace()
    assert not (tmp_path / "plan.json").exists()          # 产物被清
    assert (tmp_path / "my_notes.txt").exists()           # 用户文件保住
