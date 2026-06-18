"""
本地 JSON 上下文读写(替代后端 MongoDB)

后端各工具从 Mongo 的 user_events / host_profiles / pre_eventplanner / ... 读上下文;
单机版改成读工作目录下的本地 JSON 文件:
    event.json   —— 活动基础信息(theme/attendees/time/location/language/event_name…)
    host.json    —— 主办方(host_name/industry/host_profile)
    plan.json    —— 各 skill 的产物累加器(skill 写、其它 skill 读)
    inspiration.json —— 调研类(趋势/痛点)产物

工作目录(沙箱):
- 缺省落在**系统临时区**的 loevent-workspace/(不再写进项目目录,私密业务数据用完即清);
- `LOEVENT_WORKDIR` 显式指定时以它为准(覆盖默认沙箱);
- `LOEVENT_SESSION` 给沙箱再分一层子目录,便于多活动并行时互不串档。
同一次任务内,各 skill 靠这个目录里的 json 互相传递结果(plan.json 共享工作区);
任务结束 / 换新活动时调 clear_workspace()(或 `python -m engine.context_local --clear`)擦掉。
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

# 缺省把产物写进临时沙箱,而不是当前项目目录:私密活动/主办方/受众数据不长期落盘
_SANDBOX_ROOT_NAME = "loevent-workspace"

# clear_workspace 在「用户自定义 workdir」时只删这些 loevent 自己的产物,不动目录里的其它文件
_ARTIFACT_FILES = (
    "event.json", "host.json", "plan.json", "eventplan.json", "inspiration.json",
    "audience.json", "budget.json", "poster.json", "host_bio.json", "luma.json",
    "company.json", "guests.json",
)


def _is_custom_workdir() -> bool:
    """用户是否用 LOEVENT_WORKDIR 显式指定了工作目录(决定清理时是整盘擦还是只擦产物)。"""
    return bool(os.environ.get("LOEVENT_WORKDIR", "").strip())


def workdir() -> Path:
    custom = os.environ.get("LOEVENT_WORKDIR", "").strip()
    if custom:
        d = Path(custom).resolve()
    else:
        d = Path(tempfile.gettempdir()) / _SANDBOX_ROOT_NAME
        session = os.environ.get("LOEVENT_SESSION", "").strip()
        if session:
            d = d / session
        d = d.resolve()
    d.mkdir(parents=True, exist_ok=True)
    return d


def clear_workspace() -> Path:
    """擦掉当前工作沙箱(任务结束 / 换新活动时调用)。

    默认沙箱(系统临时区)→ 整盘 rmtree;
    用户用 LOEVENT_WORKDIR 自定义的目录 → 只删 loevent 自己的产物,绝不动目录里的其它文件
    (避免误删用户指定目录下的无关内容)。
    """
    d = workdir()
    if not _is_custom_workdir():
        shutil.rmtree(d, ignore_errors=True)
        return d
    for name in _ARTIFACT_FILES:
        (d / name).unlink(missing_ok=True)
    for produced in list(d.glob("poster_*.png")) + list(d.glob("*_input.json")):
        produced.unlink(missing_ok=True)
    return d


def load_json(name: str, *, required: bool = False) -> Optional[Dict[str, Any]]:
    """读工作目录下的 <name>.json;不存在时 required=True 抛错,否则返回 None。"""
    path = workdir() / (name if name.endswith(".json") else f"{name}.json")
    if not path.exists():
        if required:
            raise FileNotFoundError(
                f"缺少 {path.name}(在 {path.parent})。请先在该工作目录跑 skill-init "
                f"(把活动描述变成 event.json/host.json/plan.json)。"
            )
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        # 文件被截断/手改坏 → 给清晰报错,别让裸 JSONDecodeError 冒泡
        raise ValueError(f"{path.name} 不是合法 JSON({path}): {e}") from e


def save_json(name: str, data: Dict[str, Any]) -> Path:
    """把结果写进工作目录下的 <name>.json(skill 的产物落地点)。"""
    path = workdir() / (name if name.endswith(".json") else f"{name}.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        # 磁盘满 / 无写权限 → 别静默,显式抛(否则 skill 会"假成功")
        raise OSError(f"写入 {path} 失败(检查磁盘空间/写权限): {e}") from e
    return path


def merge_into(name: str, patch: Dict[str, Any]) -> Path:
    """把 patch 合并进 <name>.json(用于 plan.json 累加器:谁产出谁 merge)。"""
    current = load_json(name) or {}
    current.update(patch)
    return save_json(name, current)


if __name__ == "__main__":
    import sys

    if "--clear" in sys.argv:
        cleared = clear_workspace()
        print(f"已清空 LoEvent 工作沙箱:{cleared}")
    else:
        print(f"当前工作沙箱:{workdir()}")
