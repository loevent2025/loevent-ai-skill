"""config_loader.safe_render:Jinja2 沙箱渲染,防 prompt 注入(安全相关)。"""

import pytest
from jinja2.exceptions import SecurityError

from engine.config_loader import safe_render


def test_normal_render():
    assert safe_render("Hello {{ name }}", name="World") == "Hello World"


def test_user_input_is_data_not_template():
    # 用户输入里的 {{ }} 应被当成纯文本,不能二次执行(否则就是注入)
    assert safe_render("{{ x }}", x="{{ 7*7 }}") == "{{ 7*7 }}"


def test_sandbox_blocks_escape_chain():
    # 经典沙箱逃逸链(__mro__/__subclasses__/__globals__)应被 Jinja2 沙箱拦下;
    # 用普通 Environment 这里就能拿到类层级、进而 RCE。这条证明用的是 SandboxedEnvironment。
    with pytest.raises(SecurityError):
        safe_render("{{ ''.__class__.__mro__ }}")
    with pytest.raises(SecurityError):
        safe_render("{{ {}.__class__.__init__.__globals__ }}")
