"""
Prompt 加载 + Jinja2 沙箱渲染

- load_yaml: 读 engine/config/ 下的 prompt YAML(逐字复制自后端 config/)
- safe_render: 沙箱化 Jinja2,防止用户输入里的 {{ }}/{% %} 被执行(prompt 注入)

两者与后端 helpers/load_yaml.py、helpers/safe_template.py 行为一致。
"""

from functools import lru_cache
from pathlib import Path

import yaml
from jinja2.sandbox import SandboxedEnvironment

# 锚定到 engine/config/(随 bundle 走,不依赖后端目录)
_CONFIG_DIR = Path(__file__).resolve().parent / "config"

_env = SandboxedEnvironment(keep_trailing_newline=True, autoescape=False)


@lru_cache(maxsize=None)
def load_yaml(file_name: str):
    """加载 engine/config/ 下的 YAML(进程级缓存:均为静态 prompt 模板)。"""
    yaml_path = _CONFIG_DIR / file_name
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"{file_name} not found at {yaml_path} —— 该 skill 需要的 prompt YAML "
            f"没被复制进 engine/config/,请补齐。"
        )


def safe_render(template_str: str, **kwargs) -> str:
    """沙箱化渲染 Jinja2 模板字符串。"""
    template = _env.from_string(template_str)
    return template.render(**kwargs)


def config_path(*parts) -> "Path":
    """返回 engine/config/ 下的资源路径(如 style 知识库 md)。

    后端 poster 把 style md 路径写死成 services/ai_tools/config/poster_tool/...;
    bundle 内改用本函数解析,随 bundle 走。
    """
    return _CONFIG_DIR.joinpath(*parts)
