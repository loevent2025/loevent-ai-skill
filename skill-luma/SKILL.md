---
name: loevent-luma
description: 为活动生成 Luma 风格的发布文案——短文案(50-100 字社媒钩子)、长文案(200-300 字完整介绍,含议程/嘉宾/CTA)与一句话标题。当用户说"写活动介绍/帮我出 Luma 文案/活动发布文案/活动描述"时用。需要先有活动档案(用 loevent-init 生成);长文案还需要活动的议程/嘉宾等原始素材。
version: 0.1.0
metadata:
  hermes:
    tags: [copywriting, events, marketing, luma, content]
    category: content-creation
    requires_toolsets: [terminal]
required_environment_variables:
  - name: GEMINI_API_KEY
    prompt: 你的 Google Gemini API Key
    help: 在 https://aistudio.google.com/apikey 申请
    required_for: 全部功能
---

# LoEvent · Luma 活动文案(luma)

从活动信息生成可直接发布的 Luma 文案:
- **短文案**(`luma_event_description_short`):50-100 字,Hook + 收益点 + 受众 + CTA,适合社媒/卡片。
- **长文案**(`luma_event_description_long`):200-300 字,完整介绍(开场 → 体验 → 收益 → 议程 → 嘉宾 → 详情 → 受众 → CTA)。
- **标题**(`luma_event_title`):一句话核心命题,≤140 字符。

## 何时使用(When to Use)
- 用户想要活动的发布文案 / Luma 介绍 / 活动描述时。
- **前置依赖**:工作目录要有 `event.json` 和 `host.json`(没有就先调 **loevent-init** 把用户的活动描述抽成档案,再回来跑本工具)。

## ⚠️ 先讲清:短文案总能出,长文案要有素材
- **短文案**只依赖 `event.json` + `host.json`,任何情况下都能生成。
- **长文案是两步生成**:先从「活动原始素材」(议程、嘉宾、详情等)抽出结构化字段,再写成完整文案。
  - 素材来源优先级:`--raw-text-file` / `description_input.json` 的 `raw_text` > `plan.json` 内的 `ai_extracted.raw_text` 或 `html_content`。
  - **没有任何素材 → 自动降级,只出短文案**(不是报错)。这时你(Claude)要提示用户:补一段议程/嘉宾文本即可补出长文案。

## 缺东西先弹窗问,别报错也别瞎填(AskUserQuestion)
**缺 `GEMINI_API_KEY` 的处理见 [`references/API-KEY.md`](../references/API-KEY.md)**:先检测、已配置就别再弹;确实缺才弹一次,给「自己改 .env / 直接粘贴」两条路,key 写进**项目根** `.env`(不是沙箱),别甩报错。
(`language` 默认取 `event.language`、长文案素材可选(没有就降级只出短文案),均不必弹窗硬问。)

## 步骤(Procedure)
1. **确认上下文**:工作目录有没有 `event.json`/`host.json`?没有 → 先用 loevent-init 生成。
2. **确定语言与素材(别瞎填)**:
   - `language`:输出语言,如 `中文` / `English`;不填则取 `event.json` 里的 `language`。
   - 想要长文案,准备活动的**议程/嘉宾/详情原始文本**。两种给法:
     - 写进工作目录的 `description_input.json`:
       ```json
       {
         "language": "中文",
         "raw_text": "9:00 AM - 签到与咖啡\n9:30 AM - 主题演讲……\n嘉宾:张三(Nova Labs CTO)……"
       }
       ```
     - 或用命令行 `--raw-text-file ./agenda.txt` 指向一个纯文本文件。
   - 若 `plan.json` 里已有素材(loevent-init 注入的 `ai_extracted.raw_text` / `html_content`),可不提供,脚本会自动取用。
3. 运行:
   ```bash
   python skill-luma/scripts/run.py
   # 或:python skill-luma/scripts/run.py --language English --raw-text-file ./agenda.txt
   ```
4. 产物:`luma.json` 写入工作目录,并把文案 merge 进 `plan.json`(供下游复用);结构化结果打印到 stdout。

## 结果呈现(Presenting Results)— 必读
**不要把脚本输出的原始 JSON 直接甩给用户。** 你(Claude)要按下面整理成可读交付:

> **✍️ 活动文案已生成**
>
> **🏷️ 标题**:〈luma_event_title〉  *(字段为空就整段省略,别显示 null)*
>
> **📣 短文案**(适合社媒/卡片)
> ```
> 〈luma_event_description_short,原样保留它的换行与 bullet〉
> ```
>
> **📄 长文案**(完整介绍)
> ```
> 〈luma_event_description_long,原样保留排版:段落空行、议程逐行、emoji 详情行〉
> ```
>
> 一句话小结:〈用人话点出这版文案的卖点角度,如"主打动手实战 + 嘉宾背书"〉。要调语气/长度/换语言告诉我重写。

要点:
- **文案本体原样呈现**(短/长都用代码块包住,保住它精心设计的换行与 bullet/emoji 排版,别压成一段)。
- **标题单独加粗一行**;**短、长各起一节**,小标题清晰。
- **字段为空就整节省略**,绝不显示 `null`。
- **只出了短文案时**(`long_content_generated` 为 false):正常给短文案,然后**一句话说明**长文案缺素材——"想要完整长文案,给我一段议程/嘉宾/详情就能补出来",**不要报错式甩 traceback**。
- 跑完可顺势提示:"要不要据此出海报 / 排时间线 / 写社媒多平台文案?"

## 易错点(Pitfalls)
- 缺 `event.json`/`host.json` → 脚本会报错提示先跑 loevent-init,照做即可。
- 长文案没出 ≠ 坏了:多半是没素材(`plan.ai_extracted.raw_text` / `plan.html_content` 为空)→ 用 `--raw-text-file` 或 `description_input.json` 的 `raw_text` 补一段即可。
- 输出语言不对 → 显式传 `--language`,或确认 `event.json` 的 `language` 字段。
- 缺 `GEMINI_API_KEY` → 先 `python engine/doctor.py`。
