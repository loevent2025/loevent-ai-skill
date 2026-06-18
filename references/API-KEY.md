# GEMINI_API_KEY 收集流程（所有 skill 共用）

各 skill 的 `SKILL.md` 在「缺东西先弹窗问」段里用一行指到本文件，避免 12 份重复。
这里规定 **Claude 在 Claude Code 里怎么处理缺 key**。

## 背景：为什么要 Claude 兜底

frontmatter 的 `required_environment_variables` 只在 Hermes / claude.ai 运行时才会触发原生填 key 弹窗，
**在 Claude Code 里不触发**，脚本自己也弹不出窗。所以 key 的收集由你（Claude）用 `AskUserQuestion` 兜底。

## 规则一：先检测，别主动问；已配置就绝不再弹

**不要一上来就问 key。** 按 skill 的步骤直接跑脚本即可——
`import engine` 时会自动从 `<项目根>/.env` 和当前目录 `.env` 读 key（见 `engine/__init__.py`）。

- 脚本能正常跑 → 说明 key 已就绪，**什么都别弹**。
- 同一会话里前面的 skill 已经写过 key（或用户早就配好）→ 它持久化在 `.env` 里，后续 skill `import` 时自动读到，**同样不要再弹**。
- 想主动复核时（可选）：`python engine/doctor.py`，它查的就是加载 `.env` 后的 `os.environ`，会打印 `✓ GEMINI_API_KEY 已设置` 或 `✗ 未检测到`。

**只有**脚本明确报「缺少 GEMINI_API_KEY」（或 doctor 显示未检测到）时，才进入下面的弹窗流程。

## 规则二：缺 key 时，弹一次，给两条路

调用 `AskUserQuestion`，`header` 用 `API Key`，给用户两个明确选项（外加自动的 Other）：

- **路 A — 我自己去 .env 填**：你把**确切文件路径**告诉用户（见规则三），让他在该文件加一行
  `GEMINI_API_KEY=AIza...`，填好回来说一声；你重新检测（直接重跑脚本或 `doctor.py`）通过后继续。
- **路 B — 我直接粘贴 Key**：让用户在卡片的 **Other** 输入框直接粘贴 Key（`AIza...`），
  你把它写进同一个 `.env` 文件，再继续。

用户也可以跳过选项、直接在 Other 里粘 Key，等同走路 B。
**任何情况下都别把缺 key 的原始报错直接甩给用户。**

## 规则三：key 写进哪个 .env（重要，别写错地方）

`engine/__init__.py` 只自动加载这两个 `.env`：当前运行目录 `cwd/.env`、和 **bundle 项目根** `<项目根>/.env`。
**它不读 LoEvent 的「工作目录 / 沙箱」**（那是放 event/host/plan.json 的临时目录，不是 key 的来源）。

所以 key 一律写进 **bundle 项目根的 `.env`**——它不管你从哪运行都会被读到，最可靠。

- 项目根 = 各 `skill-*/` 和 `engine/` 的上一级目录，也就是 `requirements.txt` / `.env.example` 所在目录。
- 路 A 给用户的就是这个绝对路径下的 `.env`；路 B 你也写到这里。
- 文件不存在就新建；存在就**追加 / 更新** `GEMINI_API_KEY` 这一行，别覆盖掉用户已有的其它配置。
