# AGENTS.md — LoEvent AI Skills 的 agent 公约

> 给**任何** AI coding agent(Claude Code / Codex / Cursor / Gemini·Antigravity / Aider …)看的统一说明:
> 怎么配环境、怎么挑并调用 skill、怎么处理失败、别碰什么。engine 与 skill 脚本是受测内核,不要改。

## 这是什么

一套**活动策划** skill:用大白话描述一场活动 → 整理成结构化档案 → 受众/预算/时间线/嘉宾/文案/海报/完整方案。
每个 skill = 一段 `SKILL.md`(说明书)+ `scripts/`(干活的 Python)。skill 之间靠工作目录里的本地 JSON(`plan.json` 累加器)传上下文。本地运行、用用户自己的 Gemini Key。

## Setup(首次)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # 填 GEMINI_API_KEY(在项目根 .env;见 references/API-KEY.md)
python engine/doctor.py         # 自检:Key / 文本模型 / grounding / 图像档
```

## 工作目录(产物落哪)

- 产物(`event/host/plan.json` 等)默认落**系统临时沙箱**(用完即清);`LOEVENT_WORKDIR=./某目录` 可固定留存。
- 同一活动的所有 skill **共用一个工作目录**传值。
- 换新活动前清场:`python -m engine.context_local --clear`。

## 怎么挑 skill(非 Claude Code 的 agent 看这里)

Claude Code 会自动按 `SKILL.md` 的 frontmatter 触发;**其它 agent 自己来挑**:

1. 读所有 `skill-*/SKILL.md` 的 frontmatter `description`(每条都写明"当用户说 X 时用"),与用户需求匹配,挑最贴的那个。
2. **先决条件**:工作目录没有 `event.json`/`host.json`/`plan.json` 时,**先跑 `loevent-init`** 把活动描述抽成档案,再跑别的。
3. 按那条 `SKILL.md` 的「步骤」执行,并按「结果呈现」把结构化 JSON 整理成可读中文给用户(**别直接甩 JSON**)。

## 怎么调用一个 skill

```bash
python skill-<name>/scripts/run.py [参数]
```

**例外**:
- `skill-init` 的入口是 `init_event.py`(不是 run.py):`python skill-init/scripts/init_event.py --text "活动描述…"`
- `skill-poster` 有两个:`run.py`(出图)+ `poster_text.py`(海报文字可编辑:`ocr`/`erase`/`render`/`preview` 子命令,见其 SKILL.md)

13 个 skill:start(导览)/ init / audience / trends / host-bio / budget / timeline / company / guests / luma / social / poster / eventplanner。
**主线**:`init → audience → company →(让用户选一张策略 vibe 卡)→ eventplanner`;其余按需穿插。

## 主动导览 / 推进(别假设用户已懂流程)

冷启动的用户/agent 不知道有哪些 skill、什么顺序。所以:

- **用户问"怎么用 / 这是什么 / 介绍一下 / help",或明显没头绪** → 调 **`loevent-start`** 给主线地图(或直接给:`init 建档 → audience 受众 → company 主办方调研·出 3 套策略方向 → 选一套 → eventplanner 完整方案`;支线 预算/时间线/海报/社媒/嘉宾 随时点)。
- **每跑完一个 skill** → 主动报一句"当前在主线哪一步 + 建议的下一步",别让用户自己猜。
- **分寸**:冷启动/迷路时给完整地图;之后只给轻量"下一步建议"一句话,别每次念整张图(同 preflight 的"该出现时出现")。

## 退出码协议(脚本失败时怎么办)

脚本统一用规范退出码(见 `engine/runtime.py`):

- `0` 成功 → 读 stdout 的结构化 JSON,整理后给用户。
- `2` 缺输入(用户该补)→ 读 JSON 里的 `hint`,**用纯文本问用户补齐**,再重跑。
- `1` LLM/系统错(可重试)→ 照 `hint`,多半先 `python engine/doctor.py` 自检。
- `130` 用户中断。

> **关于"问用户"(全局规则)**:本仓 `SKILL.md` / `references/` 里凡写"用 `AskUserQuestion`(弹窗/收集)"的,
> 都只是指**向用户提问**——Claude Code 有 `AskUserQuestion` 工具会弹窗;**其它 agent 没有这个工具,一律改用普通文本提问**。
> 任何情况下别把原始报错 / traceback 甩给用户。

## Key 与参数 preflight

- **缺 `GEMINI_API_KEY`**:见 [`references/API-KEY.md`](references/API-KEY.md)(先检测、已配置别再弹;写进项目根 `.env`)。
- **参数该问/该确认/该沉默**:见 [`references/PREFLIGHT.md`](references/PREFLIGHT.md)(必问 / 必确认·建议默认可改 / 沉默 三级;对应 MCP 的 **Elicitation**,按 accept/decline/cancel 处理回应)。
- **海报文字可编辑**额外需 `GOOGLE_APPLICATION_CREDENTIALS`(GCV 服务账号 JSON,独立于 Gemini Key;**绝不提交进仓库**)。

## do-not-touch(边界)

- **别改 `engine/` 和 `skill-*/scripts/`**:这是受测内核(见 `tests/`),改它们要先跑 `pytest`。
- 深入细节看:`README.md`、对应的 `skill-*/SKILL.md`、`references/`。
- **密钥红线**:`.env`、任何 service account / `*AccountKey*.json` 绝不入库(已在 `.gitignore` 挡)。

## 测试

```bash
pip install -r requirements-dev.txt
pytest -q        # 全部 no-key / 离线,不需要任何 API key
```
