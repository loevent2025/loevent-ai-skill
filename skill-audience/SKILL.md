---
name: loevent-audience
description: 为活动推断目标受众画像(主要/次要/延伸人群 + 各自痛点)。当用户问"这个活动该面向谁/帮我做受众画像/受众定位"时用。需要先有活动档案(用 loevent-init 生成)。
version: 0.1.0
metadata:
  hermes:
    tags: [audience, events, marketing, research]
    category: research
    requires_toolsets: [terminal]
required_environment_variables:
  - name: GEMINI_API_KEY
    prompt: 你的 Google Gemini API Key
    help: 在 https://aistudio.google.com/apikey 申请
    required_for: 全部功能
---

# LoEvent · 目标受众画像(audience)

根据活动信息 + 用户的增长目标,推断主/次/延伸三层受众及其痛点。

## 何时使用(When to Use)
- 用户想知道活动该面向哪些人群、做受众定位 / GTM 画像时。
- **前置依赖**:工作目录里要有 `event.json` 和 `host.json`。没有就先调 **loevent-init**(把用户的活动描述抽成档案),再回来跑本工具——这种"缺上游就先补"的串接由你(Claude)判断。

## 缺东西先弹窗问,别报错也别瞎填(AskUserQuestion)
**缺 `GEMINI_API_KEY` 的处理见 [`references/API-KEY.md`](../references/API-KEY.md)**:先检测、已配置就别再弹;确实缺才弹一次,给「自己改 .env / 直接粘贴」两条路,key 写进**项目根** `.env`(不是沙箱),别甩报错。
**参数 preflight 见 [`references/PREFLIGHT.md`](../references/PREFLIGHT.md)**:`event_goal` / `objective` 影响产出,属**必确认(建议默认·可改)**——从 `event.json`/`plan.json` 推出草稿默认值后**摊给用户瞄一眼**(一次问完、"要改才改"),别静默填、也别硬逼他填。
**`GTMmatrix` = 前置 2×2 GTM 象限(audience 是主线上它的第一个消费者)**:见 [`references/GTM-MATRIX.md`](../references/GTM-MATRIX.md)。
- **`plan.gtm` 已有**(用户之前选过)→ **沉默复用,别重复问**;
- **没有** → 用 `AskUserQuestion`(header `GTM象限`)把「早期·获取 / 早期·留存 / 成熟·获取 / 成熟·留存」四格作为选项让用户选一格(想微调强度就 Other 填 value)。选定后本工具会写进 `plan.gtm`,eventplanner 复用。

## 步骤(Procedure)
1. **先确认上下文**:工作目录有没有 `event.json`/`host.json`?没有 → 先用 loevent-init 生成。
2. **采集三个输入(向用户问清,别瞎填)**:
   - `event_goal`:活动目标类型,`product`(产品)/ `ecosystem`(生态)/ `brand`(品牌);
   - `prompt_objective`:一句话目标(如"拉新一批 AI 开发者并转化试用");
   - `GTMmatrix`:增长坐标——增长模式(label+0~50 的值)、生命周期(label+0~50 的值)。
   把它们写进工作目录的 `audience_input.json`:
   ```json
   {
     "event_goal": "product",
     "prompt_objective": "拉新 AI 开发者并转化试用",
     "GTMmatrix": {
       "growth_mode": {"label": "获取", "value": 40},
       "lifecycle":   {"label": "早期", "value": 30}
     }
   }
   ```
   (也可改用 `--goal/--objective/--growth-label/--growth-value/--lifecycle-label/--lifecycle-value` 命令行参数。)
3. 运行:
   ```bash
   python skill-audience/scripts/run.py
   ```
4. 产物 `audience.json` 写入工作目录,并 merge 进 `plan.json`(供下游工具复用);结构化结果打印到 stdout。

## 结果呈现(Presenting Results)— 必读
**不要把脚本输出的原始 JSON 直接甩给用户。** 你(Claude)要把它整理成清晰的分层小结,例如:

> **🎯 目标受众画像**
>
> **① 核心人群(主要)**
> - 〈人群标签,逐条列〉
> - **痛点**:〈primary.painpoint,一句话〉
>
> **② 次要人群**
> - 〈逐条〉
> - **痛点**:〈secondary.painpoint〉
>
> **③ 延伸人群**
> - 〈逐条〉
> - **痛点**:〈extended.painpoint〉
>
> 一句话总结:这场活动应优先抓住〈核心人群〉,内容与嘉宾围绕他们的"〈核心痛点〉"设计。

要点:
- **三层分明**(主/次/延伸),每层先列人群、再点出痛点;
- 人群标签用 bullet,**痛点加粗前缀**;
- 末尾给一句**可执行的总结建议**(帮用户把画像落到内容/嘉宾决策上);
- 字段为空就略过,不显示 `null`;
- 跑完可顺势提示:"要不要据此排时间线 / 写社媒文案 / 出预算?"

## 易错点(Pitfalls)
- 缺 `event.json`/`host.json` → 脚本会报错提示先跑 loevent-init,照做即可。
- `GTMmatrix` 的两个 value 是 0~50 的强度,别填成百分比;不确定就向用户确认,别默认。
- 缺 `GEMINI_API_KEY` → 先 `python engine/doctor.py`。
