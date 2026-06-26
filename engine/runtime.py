"""
共享运行时(生产级):结构化输出健壮解析 + skill 顶层错误兜底。

所有 skill 用这两个 helper 收口审查发现的两个系统性问题:
  1) `json.loads(resp.text)` 对非法/截断 JSON 直接崩 → `parse_structured`(容错 + finish_reason 提示);
  2) 无顶层 try/except、失败裸 traceback → `run_skill_main`(结构化 {ok:false} + 规范退出码)。
"""

import asyncio
import json


def _strip_json_fence(text: str) -> str:
    """剥 ```json ... ``` 围栏 / 截取首个 {...},容忍 fallback 模型偶发的非纯 JSON。"""
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t[:4].lower() == "json":
            t = t[4:]
    i, j = t.find("{"), t.rfind("}")
    return t[i:j + 1] if 0 <= i < j else t


def parse_structured(resp, model_cls=None):
    """健壮解析 LLMResponse 的结构化输出。

    - 传 model_cls(Pydantic BaseModel)→ 返回**已校验实例**(调用方可 .model_dump());
      不传 → 返回 dict。
    - 容错:原文解析失败时,剥围栏 / 取首个 {...} 再试一次;
      仍失败抛带 finish_reason 的清晰异常(MAX_TOKENS 会提示被截断),交上层兜底。
    """
    text = getattr(resp, "text", "") or ""
    fr = getattr(resp, "finish_reason", None)

    def _do(s):
        return model_cls.model_validate_json(s) if model_cls is not None else json.loads(s)

    try:
        return _do(text)
    except Exception:
        try:
            return _do(_strip_json_fence(text))
        except Exception as e:
            hint = "(输出超长被截断 MAX_TOKENS,建议调小请求/拆分或重试)" if fr == "MAX_TOKENS" else ""
            raise RuntimeError(
                f"结构化输出解析失败 finish_reason={fr}{hint}: {type(e).__name__}: {e}"
            ) from e


def run_skill_main(main_coro_factory) -> int:
    """跑 skill 的 async _main,把异常转成结构化 {ok:false,...} + 规范退出码。

    用法:  if __name__ == "__main__": raise SystemExit(run_skill_main(_main))
    退出码:0 成功 / 2 缺输入(用户该补) / 1 LLM/系统错(可重试) / 130 中断。
    """
    try:
        return asyncio.run(main_coro_factory())
    except FileNotFoundError as e:
        print(json.dumps(
            {"ok": False, "error": "MissingContext", "message": str(e),
             "hint": "缺上下文文件:请先在当前工作目录跑 loevent-init,生成 event/host/plan.json。"},
            ensure_ascii=False, indent=2))
        return 2
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        print(json.dumps(
            {"ok": False, "error": type(e).__name__, "message": str(e),
             "hint": "可能是 Key 无权限/配额或网络问题;先跑 python engine/doctor.py 自检后重试。"},
            ensure_ascii=False, indent=2))
        return 1


def is_no_issues(text: str) -> bool:
    """grounding 二次核查 step1 的「无问题」判定(trends/guests/company 共用)。

    后端契约是返回固定串 "NO_ISSUES",但 grounding 模型偶发会包 ```围栏```、成对引号、
    前后空白甚至句末标点,直接 == 比对会把「无问题」误判成「有问题」、白触发一次 FIX。
    这里统一剥掉围栏/引号/空白/标点再大小写无关比对。
    """
    t = (text or "").strip().strip("`").strip()
    t = t.strip("\"'“”‘’").strip()
    t = t.rstrip("。.!！").strip()
    return t.upper() == "NO_ISSUES"
