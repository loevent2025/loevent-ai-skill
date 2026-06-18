"""
LoEvent AI Skill —— 共享内核(engine)

所有 skill 都依赖这一份内核。它把 AI 能力做成「单机化」形态:
- 用单个 GEMINI_API_KEY 直连(无多项目 Key 池 / 无按用户路由);
- 把写数据库的 token/错误日志改成可选回调(默认不做);
- 上下文不查数据库,改读本地 JSON 文件。

提示词(prompt)、输出格式(schema)、生成逻辑与后端保持一致(逐字复制),
所以「拆出来」对产出质量没有损耗。
"""

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
from .runtime import parse_structured, run_skill_main
from . import model_config
from . import context_local

__all__ = [
    "get_llm_client",
    "LLMResponse",
    "load_yaml",
    "safe_render",
    "parse_structured",
    "run_skill_main",
    "model_config",
    "context_local",
]
