---
name: loevent-budget
description: 为活动估算分项预算(任务级 低估/高估 + 9 大类目 + 是否可赞助抵扣 + 类别汇总 + 风险信号),也支持在已有预算上按一句话指令调整(整体压价/分类增减/单项改写)。当用户说"帮我做个预算/这场活动要花多少钱/出个费用估算/预算压到 X 万/餐饮砍 30%"时用。需要先有活动档案(用 loevent-init 生成 event.json/host.json);有全案/结构化提取源(plan.json)时估得更准,没有也能跑。
version: 0.1.0
metadata:
  hermes:
    tags: [budget, cost, finance, events, planning]
    category: planning
    requires_toolsets: [terminal]
required_environment_variables:
  - name: GEMINI_API_KEY
    prompt: 你的 Google Gemini API Key
    help: 在 https://aistudio.google.com/apikey 申请;系数与场地走联网搜索(grounding),普通文本档 Key 即可
    required_for: 全部功能(联网搜索失败会自动降级,不阻塞)
---

# LoEvent · 活动分项预算(budget)

把活动信息(+ 可选的全案/结构化提取源)折算成一份分项预算:每条任务给 低估/高估、归入 9 大类目、标注是否可赞助抵扣,并附类别汇总与风险信号。

## 何时使用(When to Use)
- 用户想知道"这场活动大概要花多少钱"、要一份可执行的费用清单时。
- 用户想在**已经生成的预算**上调价:"整体压到 8 万以下"、"餐饮砍 30%"、"把场地降到 5 万"、"去掉 After Party"——走 `--regenerate`。
- **前置依赖**:工作目录要有 `event.json` 和 `host.json`(没有就先调 **loevent-init**)。
  `plan.json` 是可选的"提取源":里面若有上游全案(`html_content`)或结构化字段(`ai_extracted`),预算会更贴合方案;没有也能基于活动信息 + 静态模板 + 系数出一份基线预算。

## ⚠️ 先讲清两件事(降级与简化,务必先告诉用户)
1. **系数与场地走联网搜索(grounding)**:城市消费水平、规模、档次、汇率、场地实际报价都靠实时搜索。
   - 搜索/解析**失败会自动降级**:改用一组中性系数(全 1.0、汇率按 CNY 1:1),仍产出预算,只是金额未做地区/汇率校准——**这不是报错**,要如实告诉用户"金额未经地区校准,仅供参考"。
   - 先跑 `python engine/doctor.py` 确认 Key 与联网可用。
2. **单机版做了两处简化(对齐 v1 方案)**:
   - **不联网下载历史预算 Excel**:`historical_budgets` 始终为空,因此预算**不做历史分布校准**(信号里会标注"无历史预算参考")。
   - **解析全案 HTML 需要 `bs4`**:没装 `beautifulsoup4` 时跳过 HTML 解析,改走 `ai_extracted` 或空提取源——不崩,但 `html_content` 这条源会被忽略。

## 缺东西先弹窗问,别报错也别瞎填(AskUserQuestion)
**缺 `GEMINI_API_KEY` 的处理见 [`references/API-KEY.md`](../references/API-KEY.md)**:先检测、已配置就别再弹;确实缺才弹一次,给「自己改 .env / 直接粘贴」两条路,key 写进**项目根** `.env`(不是沙箱),别甩报错。
(`--regenerate` 调整指令、提取源都可选,均不必弹窗硬问;用户想压价时把他那句话原样传给 `--regenerate` 即可。)

## 步骤(Procedure)
1. **确认上下文**:工作目录有没有 `event.json`/`host.json`?没有 → 先用 loevent-init 生成。
2. **看有没有提取源(可选,提准用)**:
   - 若上游(全案/init)已写过 `plan.json`,里面可能带 `source` / `ai_extracted` / `html_content`,脚本会自动读。
   - 想手动喂提取源,就照 `templates/budget_input.json` 在工作目录放一份 `budget_input.json`:
     ```json
     {
       "source": "ai_extracted",
       "ai_extracted": {
         "content": "Day1 主论坛+workshop;Day2 黑客松+颁奖晚宴",
         "marketing": "社媒预热 + 1 位 KOL + 宣传短视频",
         "venues": {"confirmed": null, "recommended": "市中心联合办公空间,含基础 AV"},
         "partners": "1 家云厂商赞助算力,1 家媒体分发"
       },
       "html_content": ""
     }
     ```
     - `source: "ai_extracted"` → 走结构化源(`content`/`marketing`/`venues`/`partners`);
     - 不填或填别的 + 提供 `html_content`(全案 HTML)→ 走全案解析(需 `bs4`)。
   - 两者都没有也行——脚本基于活动信息 + 静态模板 + 系数出一份基线预算。
3. **全新生成**:
   ```bash
   python skill-budget/scripts/run.py
   ```
4. **在已有预算上调整**(需先跑过一次、有 `budget.json`/`plan.budget`):
   ```bash
   python skill-budget/scripts/run.py --regenerate "整体压到 8 万以下,餐饮减 30%"
   ```
   (也可把指令写进 `budget_input.json` 的 `regeneration_prompt`。调整只改 `price_high`,应急预备金自动联动重算。)
5. 产物:`budget.json` 写入工作目录,并 merge 进 `plan.json`(供下游复用);结构化结果打印到 stdout。

## 结果呈现(Presenting Results)— 必读
**不要把脚本输出的原始 JSON 直接甩给用户。** 你(Claude)要把它整理成清晰的预算小结。结构化结果通常含 `task_list`(逐条任务)、可能还有 `category_summary` / `budget_total` / `signals`(取决于模型产出)。建议这样组织:

> **💰 活动预算估算**
>
> **总览**:低估约 〈budget_total.low_total〉 — 高估约 〈budget_total.high_total〉 〈unit〉
> (若有 `signals.distribution_warning` 提到"未经地区校准/无历史参考",在这里用一句话提醒。)
>
> **分项明细**(按类目归并,逐条):
> **① 场地及空间**
> - 〈task〉:〈low_estimate〉–〈high_estimate〉 〈unit〉 · 可赞助抵扣:〈sponsorship_deductible〉
> **② 餐饮服务**
> - …(其余类目同理,只列**有内容**的类目)
>
> **类别占比**(若有 `category_summary`):用一两句话点出"大头在哪"(如"餐饮+场地占了约 60%")。
>
> **⚠️ 风险提示**(若有 `signals`):
> - 弱匹配/未匹配的任务:提醒"这几项是 AI 类比估的,落地前请拿真实报价替换"。
>
> 一句话建议:〈如"主要可压缩空间在 X;若想压到 Y 万,优先砍 Z"〉。

要点:
- **按 9 大类目归并**再列任务(场地及空间 / 餐饮服务 / 技术与视听 / 内容与演讲嘉宾 / 人员劳务 / 营销与传播 / 物料与印刷品 / 交通与住宿 / 应急与其他),别一长串平铺;
- 每条给 **低估–高估 + 货币**,赞助可抵扣有值才显示;
- **空字段一律省略**,不要显示 `null` / `—` / 空类目;
- 末尾给一句**可执行建议**(哪里能省、压到目标价该砍什么);
- **调整模式**(`--regenerate`)产出通常只有 `task_list`:对比改了哪些项、新的总额,而不是重列全表;
- 跑完可顺势提示:"要不要据此做风险体检 / 排时间线 / 找赞助?"

## 易错点(Pitfalls)
- 缺 `event.json`/`host.json` → 脚本会报错提示先跑 loevent-init,照做即可。
- 金额"看起来很整/不分地区" → 多半是系数搜索降级了(用了中性系数)。如实告诉用户"未经地区与汇率校准",建议补网络后重跑。
- `html_content` 没被用上 → 大概率没装 `bs4`(`pip install beautifulsoup4`),或全案 HTML 结构不含 `div.section`;不影响出预算,只是少了全案这条源。
- `--regenerate` 报"找不到已有预算" → 先不带参数跑一次生成 `budget.json`,再调整。
- 缺 `GEMINI_API_KEY` 或联网不通 → 先 `python engine/doctor.py`。
