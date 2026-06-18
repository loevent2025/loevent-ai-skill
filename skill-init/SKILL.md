---
name: loevent-init
description: 把用户一段活动描述(文字/计划/邀请函)抽成结构化的本地活动档案(event.json / host.json / plan.json),作为其它 LoEvent 工具的输入起点。当用户说"我有一个活动想…/这是我的活动信息/帮我整理这个活动"时先用它。
version: 0.1.0
metadata:
  hermes:
    tags: [events, extraction, setup]
    category: productivity
    requires_toolsets: [terminal]
required_environment_variables:
  - name: GEMINI_API_KEY
    prompt: 你的 Google Gemini API Key
    help: 在 https://aistudio.google.com/apikey 申请
    required_for: 全部功能
---

# LoEvent · 活动初始化(init)

把用户的活动描述抽成本地档案,供 LoEvent 系列工具(受众/预算/时间线/海报…)消费。

## 何时使用(When to Use)
- 用户第一次提到一个活动、想让 LoEvent 工具帮忙时,**先跑这个**;
- 工作目录里还没有 `event.json` / `host.json` / `plan.json` 时。
- 如果用户只想要某个单项能力(如只算预算)且这些文件已存在,**不必**重复跑。

## 准备(Setup)
- 首次使用前,按 `references/SETUP.md`(bundle 根)建好环境、填好 `GEMINI_API_KEY`。
- 产物默认写进**系统临时沙箱**(`loevent-workspace/`),不再落进项目目录;`LOEVENT_WORKDIR` 可覆盖。同一活动的所有工具共用这个沙箱传值。

## 存储与生命周期(短暂沙箱,务必照此编排)
产物(`event/host/plan.json` 等)是**会话级短暂存储**,默认在系统临时沙箱里,不长期保存。你(Claude)按这套编排:
- **开一个新活动前**:先 `python -m engine.context_local --clear` 擦掉上一个活动的沙箱,**绝不把上个活动的档案带进新活动**。
- **同一个活动内、用户提新的子需求**(如已做受众、现在要海报):**复用**沙箱里的 `event/host/plan.json`,**只重新生成被点名的那个产物**(海报/文案/预算每次跑本就覆盖重生);**不要**把 company(20+ 次联网)/trends/guests 这种重调研无谓重跑——又慢又烧 Key。
- **任务收尾**:活动做完、用户表示告一段落时,跑一次 `--clear` 把私密业务数据擦掉(像模型那样用完不留痕)。
- 用户想长期留档:让他显式设 `LOEVENT_WORKDIR=./某目录`(设了就不自动擦整盘,只清 loevent 产物)。

## 缺东西先弹窗问,别报错也别瞎填(AskUserQuestion)
在 Claude Code 里,frontmatter 的 `required_environment_variables` **不会**触发原生填 key 弹窗(那是 Hermes/claude.ai 运行时的能力),脚本自己也弹不出窗。需要时由你(Claude)调用 `AskUserQuestion` 收集:
- **缺 `GEMINI_API_KEY`**:header `API Key`、让用户在 **Other** 里粘贴 Key → 写进工作目录 `.env`(`GEMINI_API_KEY=AIza...`,`load_dotenv` 下次跑自动读)再继续,**别把缺 key 的报错直接甩给用户**。
- **没有活动描述**(本工具唯一的必填输入):用户只说"帮我弄个活动"却没给任何细节时,调 AskUserQuestion 让他补一段描述(时间 / 地点 / 主题 / 主办方 / 规模,用 Other 自由填),**别自己编一个活动**。

## 步骤(Procedure)
1. 拿到用户的活动描述。可以是一段话、一份计划、一封邀请函——**原文喂进去即可**,不用自己先总结。
2. 运行(任选其一):
   ```bash
   python skill-init/scripts/init_event.py 活动描述.txt
   # 或
   python skill-init/scripts/init_event.py --text "9月20日在上海办一场面向AI开发者的发布会，主办方是…"
   ```
3. 脚本会在工作目录写出 `event.json` / `host.json` / `plan.json`,并把结构化结果打印到标准输出(JSON)。

## 结果呈现(Presenting Results)— 必读
**不要把脚本输出的原始 JSON 直接贴给用户。** 你(Claude)要把它整理成一段清爽、好读的中文小结,例如:

> **活动已识别 ✅**
> - **名称**:〈event_name〉  ·  **主题**:〈theme〉
> - **时间**:〈time_start〉 → 〈time_end〉(〈timezone〉)
> - **地点**:〈location〉  ·  **预计人数**:〈attendees〉  ·  **语言**:〈language〉
> - **主办方**:〈host_name〉(〈industry〉)
> - **场景/规模**:〈scene_type〉 / 〈event_scale〉
>
> 已生成本地档案(event/host/plan.json)。接下来可以:做受众画像、出预算、排时间线、写社媒文案、生成海报……要哪个?

要点:
- 用**分点 + 关键字段加粗**,不要表格化的原始键名(如 `time_start`),要说"时间";
- 字段缺失就**省略那一行**,不要显示空值或 `null`;
- 结尾**主动列出下一步能做什么**(对应其它 skill),引导用户继续。

## 易错点(Pitfalls)
- 缺 `GEMINI_API_KEY` → 先跑 `python engine/doctor.py` 自检。
- 单机版**不做**地理编码(经纬度留空),这是预期行为,不是错误。
- 抽取依赖模型理解,**字段可能不全**;呈现时如实说明"未识别到 X,可以补充告诉我"。
