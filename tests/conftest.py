"""pytest 公共装置:只做两件事——把仓库根加进 sys.path、提供按路径加载 skill 脚本的 fixture。

这些测试全部 **no-key / 离线**:只调确定性函数、读本地文件,不触发任何模型 API,CI 可裸跑。
(保持本文件极简、可审:不做任何网络/隐式执行,避免成为供应链攻击面。)
"""

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture
def load_script():
    """按相对路径加载一个 skill 脚本(它们是脚本不是包,只能按文件路径导入)。"""
    def _load(relative_path: str):
        path = REPO_ROOT / relative_path
        module_name = relative_path.replace("/", "_").replace(".py", "")
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return _load
