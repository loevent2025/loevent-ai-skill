# 模型配置 / Key 收集流程（所有 skill 共用）

各 skill 的 `SKILL.md` 在「缺东西先弹窗问」段里用一行指到本文件，避免 12 份重复。
这里规定 **agent 怎么处理"没配好模型"**(Claude Code 及任何读 AGENTS.md 的 agent 通用)。

本文件覆盖两条路:
- **默认走 Gemini**(海外):只需 `GEMINI_API_KEY` —— 见规则一~三;
- **用 Gemini 以外的模型**(国内用户常用,如 GLM/DeepSeek/豆包):填一组 `LOEVENT_TEXT_*` 等环境变量 —— 见规则四。

冷启动、且**两者都没配**时,先按**规则零**问用户用哪个,别默认假设有 Gemini。

## 背景：为什么要 agent 兜底

frontmatter 的 `required_environment_variables` 只在 Hermes / claude.ai 运行时才会触发原生填 key 弹窗，
**在 Claude Code 里不触发**，脚本自己也弹不出窗。所以 key 的收集由 **agent 向用户提问**兜底(Claude Code 用 `AskUserQuestion` 弹窗;其它 agent 直接用文本问)。

## 规则零：冷启动且没配任何模型时，先问"用哪个模型"

**仅当**检测到**既没有 `GEMINI_API_KEY`、也没有 `LOEVENT_TEXT_PROVIDER`/`LOEVENT_TEXT_BASE_URL`** 时触发
(可先 `python engine/doctor.py` 判:它会明说"既未配 LOEVENT_TEXT_PROVIDER 也没有 GEMINI_API_KEY")。

向用户问一次(Claude Code 用 `AskUserQuestion`,`header` 用 `模型`;其它 agent 用文本),给三选项:
- **Gemini(海外)** → 走规则一~三收 `GEMINI_API_KEY`;
- **国内模型(GLM / DeepSeek / Kimi / 豆包…)** → 走规则四收 `LOEVENT_TEXT_*`;
- **自定义 / 网关(OneAPI·OpenRouter)** → 走规则四,但填 `LOEVENT_TEXT_BASE_URL`。

**已配好任一**(脚本能跑 / doctor 显示某条路 OK)→ **什么都别问**,直接干活。别每次念这套(同 preflight「该出现时出现,别唠叨」)。

## 规则一：先检测，别主动问；已配置就绝不再弹

**不要一上来就问 key。** 按 skill 的步骤直接跑脚本即可——
`import engine` 时会自动从 `<项目根>/.env` 和当前目录 `.env` 读 key（见 `engine/__init__.py`）。

- 脚本能正常跑 → 说明 key 已就绪，**什么都别弹**。
- 同一会话里前面的 skill 已经写过 key（或用户早就配好）→ 它持久化在 `.env` 里，后续 skill `import` 时自动读到，**同样不要再弹**。
- 想主动复核时（可选）：`python engine/doctor.py`，它查的就是加载 `.env` 后的 `os.environ`，会打印 `✓ GEMINI_API_KEY 已设置` 或 `✗ 未检测到`。

**只有**脚本明确报「缺少 GEMINI_API_KEY」（或 doctor 显示未检测到）时，才进入下面的提问流程。

## 规则二：缺 key 时，弹一次，给两条路

向用户提问(Claude Code 用 `AskUserQuestion`、`header` 用 `API Key`,带自动的 Other;其它 agent 直接用文本问),给两个明确选项：

- **路 A — 我自己去 .env 填**：你把**确切文件路径**告诉用户（见规则三），让他在该文件加一行
  `GEMINI_API_KEY=AIza...`，填好回来说一声；你重新检测（直接重跑脚本或 `doctor.py`）通过后继续。
- **路 B — 我直接粘贴 Key**：让用户把 Key（`AIza...`）发过来（Claude Code 在卡片的 **Other** 输入框粘贴;其它 agent 直接贴在对话里），
  你把它写进同一个 `.env` 文件，再继续。

用户也可以跳过选项、直接把 Key 贴过来，等同走路 B。
**任何情况下都别把缺 key 的原始报错直接甩给用户。**

## 规则三：key 写进哪个 .env（重要，别写错地方）

`engine/__init__.py` 只自动加载这两个 `.env`：当前运行目录 `cwd/.env`、和 **bundle 项目根** `<项目根>/.env`。
**它不读 LoEvent 的「工作目录 / 沙箱」**（那是放 event/host/plan.json 的临时目录，不是 key 的来源）。

所以 key 一律写进 **bundle 项目根的 `.env`**——它不管你从哪运行都会被读到，最可靠。

- 项目根 = 各 `skill-*/` 和 `engine/` 的上一级目录，也就是 `requirements.txt` / `.env.example` 所在目录。
- 路 A 给用户的就是这个绝对路径下的 `.env`；路 B 你也写到这里。
- 文件不存在就新建；存在就**追加 / 更新** `GEMINI_API_KEY` 这一行，别覆盖掉用户已有的其它配置。

## 规则四：用 Gemini 以外的模型(多供应商)

用户选了国内/其它模型(规则零),或脚本报 `缺 LOEVENT_TEXT_API_KEY`/`缺 model` 时,收集**一组**字段写进同一个项目根 `.env`(写法同规则三)。任意 OpenAI 兼容供应商,换 base_url 即可;**官方实测背书:Gemini、GLM;其余为「理论兼容,自行验证」**。

**① 文本 + 结构化(必填,所有纯文本 skill 用)**——三个一组:
- `LOEVENT_TEXT_PROVIDER`:preset 名 `glm`/`kimi`/`deepseek`/`qwen`/`ernie`/`doubao`/`minimax`/`openai`(base_url 自动带出);自定义/网关则改填 `LOEVENT_TEXT_BASE_URL`;
- `LOEVENT_TEXT_MODEL`:该家的模型名(按用户账号实际填,别猜);
- `LOEVENT_TEXT_API_KEY`:该家的 key。
缺 model 或 key → 脚本会明确报哪个缺,**按报错补齐那一项再重跑**,别把 traceback 甩给用户。

**② 联网调研(trends/guests/company/budget 才需要)**:非-Gemini **没有内置搜索**,要这几个 skill 出真实来源,必须配外部搜索:
- `LOEVENT_SEARCH_PROVIDER=bocha`(国内,免费 1000 次)或 `tavily`(海外)+ `LOEVENT_SEARCH_API_KEY`。
- **没配会怎样**:这些 skill 默认**报错中止**(避免无来源编造)。用户若接受无实时来源,设 `LOEVENT_ALLOW_UNGROUNDED=1`。

**③ 海报文生图(只想出海报才需要)**:
- `LOEVENT_IMAGE_PROVIDER=doubao`/`cogview`/`openai` + `LOEVENT_IMAGE_MODEL` + `LOEVENT_IMAGE_API_KEY`;海报比例可选 `LOEVENT_IMAGE_SIZE=1024x1536`。
- 海报「文字可编辑」的**消字**(可选):`LOEVENT_IMAGE_EDIT_PROVIDER=qwen` + `LOEVENT_IMAGE_EDIT_MODEL=qwen-image-edit` + `LOEVENT_IMAGE_EDIT_API_KEY`(DashScope);不配则退到 Gemini 或 poster_text 的本地 erase 兜底。

**国内默认组合(推荐)**:`LOEVENT_TEXT_PROVIDER=glm` + `LOEVENT_SEARCH_PROVIDER=bocha` + `LOEVENT_IMAGE_PROVIDER=doubao`(或 `cogview`,cogview-3-flash 免费)——全链路国内直连、都有免费档。

**分寸**:用户只想跑纯文本 skill,就只收①,别一上来逼他把搜索/图像 key 都配齐;要用到调研/海报时再按需收②③。完整字段清单见 `.env.example`。
