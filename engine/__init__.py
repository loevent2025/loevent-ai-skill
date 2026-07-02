"""
LoEvent Pro —— 共享内核(engine)

所有 skill 都依赖这一份内核。它把 AI 能力做成「单机化」形态:
- 用单个 GEMINI_API_KEY 直连(无多项目 Key 池 / 无按用户路由);
- 把写数据库的 token/错误日志改成可选回调(默认不做);
- 上下文不查数据库,改读本地 JSON 文件。

提示词(prompt)、输出格式(schema)、生成逻辑与后端保持一致(逐字复制),
所以「拆出来」对产出质量没有损耗。
"""

__version__ = "0.1.0"

# 可选:自动加载 .env(工作目录优先,其次 bundle 根)。装了 python-dotenv 才生效;
# 没装也不报错——用户也可以直接 export GEMINI_API_KEY。
try:  # pragma: no cover
    import os as _os
    from pathlib import Path as _Path
    from dotenv import load_dotenv as _load_dotenv

    _load_dotenv(_Path.cwd() / ".env")
    _bundle_root = _Path(__file__).resolve().parent.parent
    _load_dotenv(_bundle_root / ".env")
except ImportError:
    # 只容忍"没装 python-dotenv"(用户可直接 export GEMINI_API_KEY);
    # load_dotenv 对缺失的 .env 本就不报错,故不吞其它异常。
    pass

from .llm_client import get_llm_client, LLMResponse
from .config_loader import load_yaml, safe_render
from .runtime import parse_structured, run_skill_main, is_no_issues
from . import model_config
# context_local 故意不在此 eager 导入:它带 __main__ CLI(python -m engine.context_local --clear),
# 包初始化时若先导入它,runpy 再以 __main__ 执行会报 RuntimeWarning(模块已在 sys.modules)。
# 各 skill 用 `from engine import context_local` 仍能正常拿到(子模块按需导入)。

__all__ = [
    "get_llm_client",
    "LLMResponse",
    "load_yaml",
    "safe_render",
    "parse_structured",
    "run_skill_main",
    "is_no_issues",
    "model_config",
]
