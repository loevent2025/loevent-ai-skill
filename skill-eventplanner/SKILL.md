---
name: loevent-eventplanner
description: 把一场活动写成一份完整的活动策划方案——目标/背景/商业价值、内容设计(受众画像/流程/嘉宾)、场地推荐、合作赞助、营销推广共 6 个章节。当用户说"帮我写活动方案/出一份完整策划/把这场活动落成方案"时用。前置:先跑 loevent-init → loevent-audience → loevent-company,并让用户从三套策略里选一张 vibe 卡(selected_vibe)。时间线另用 loevent-timeline。
version: 0.1.0
metadata:
  hermes:
    tags: [eventplanner, proposal, planning, events, strategy]
    category: content-creation
    requires_toolsets: [terminal]
required_environment_variables:
  - name: GEMINI_API_KEY
    prompt: 你的 Google Gemini API Key
    help: 在 https://aistudio.google.com/apikey 申请;本工具是纯文本生成,普通文本档 Key 即可
    required_for: 全部功能
---

# LoEvent · 完整活动策划方案(eventplanner)

把一场活动一次性写成**一份可读的完整策划方案**,分 6 个章节:

1. **活动目标**(背景 / 短中长期目标 / 商业价值)
2. **内容设计**(受众画像 / 流程议程 / 嘉宾邀请)
3. **场地推荐**(筛选标准 + 推荐场地)
4. **时间线**(关键任务时间表 —— 本工具**不生成**,见下文)
5. **合作赞助**(理想合作方画像)
6. **营销推广**(渠道与推广策略)

每个章节由一次 LLM 调用产出:既写**章节正文**,也顺手抽出该节点要传给下游章节的**结构化字段**
(如第 1 章产出 `eventType`/`eventTone`/`organizerProfile`,供第 2/3/5/6 章复用)。各章节按
`节点1 → 节点2 → 节点3 → 节点5 → 节点6` 顺序串起来,上游字段喂给下游。

## 何时使用(When to Use)
- 用户要一份**成型的、能直接发出去的活动策划方案**;
- 已经做完前置调研(受众 + 策略方向),想把它落成正文。

## 缺东西先弹窗问,别报错也别瞎填(AskUserQuestion)
在 Claude Code 里,frontmatter 的 `required_environment_variables` **不会**触发原生填 key 弹窗(那是 Hermes/claude.ai 运行时的能力),脚本也弹不出窗。需要时由你(Claude)调用 `AskUserQuestion`:
- **缺 `GEMINI_API_KEY`**:处理见 [`references/API-KEY.md`](../references/API-KEY.md)——先检测、已配置别再弹;缺了才弹,给「自己改 .env / 直接粘贴」两条路,key 写进**项目根** `.env`(不是沙箱),别甩报错。
- **缺 `selected_vibe`**(必须三选一,见下方「人机门」):用 AskUserQuestion 把三套策略卡作为选项让用户单选,**别默认替他选**。`goal` / `objective` / `prep_date` / `user_input` 有默认或可选,不必弹窗硬问。

## 前置(Procedure)—— 这是一条流水线,缺上游要先补

本工具读工作目录下的 `event.json` / `host.json` / `plan.json`,串接关系如下:

1. **`event.json` + `host.json`** —— 活动与主办方档案。没有 → 先跑 **loevent-init**。
2. **`plan.audience`** —— 受众画像(主/次/延伸 + 痛点)。没有 → 先跑 **loevent-audience**。
3. **`plan.company`** —— 主办方调研产出的**三套策略 vibe 卡**(`brand_dna` / `competitor` /
   `trend_forward`,每张含 slogan / 互动方式 / co-host 嘉宾方向 / 建议场地)。
   没有 → 先跑 **loevent-company**。
4. **`plan.event_scale` / `plan.scene_type`** —— 规模与场景分类(通常 loevent-init / loevent-company 写)。
   缺失时降级:`event_scale` 默认 `medium`,行业知识库按 `other` 退化跳过。

### 人机门:让用户选一张 vibe 卡(关键)

`plan.company` 里有**三套策略方向卡**。本工具需要用户**明确选一张**作为本方案的调性主线
(决定 slogan、互动方式、嘉宾方向、场地类型)。这是一道**人机交互门**,由你(Claude)负责:
跑工具前,**调用 `AskUserQuestion`**(header `策略方向`),把三张卡的 `title` / `slogan` 摘要做成三个选项让用户**单选**,
把结果写进 `selected_vibe`(取值 `brand_dna` / `competitor` / `trend_forward`)。

用户没法决定时,你可给建议,但要让用户拍板;实在拿不到选择,工具会默认取第一张可用卡并在
`notes` 里提示——但**更推荐你先收集选择再跑**。

## 运行(How to Run)

```bash
# 1) 准备输入(在工作目录):event.json/host.json/plan.json 由上游 skill 生成
#    本工具的用户输入放 eventplanner_input.json(见 templates/),或用 CLI 覆盖
python skill-eventplanner/scripts/run.py \
    --selected-vibe competitor \
    --goal product \
    --objective "拉新开发者并转化框架试用" \
    --prep-date 2026-07-01
```

`eventplanner_input.json` 字段:`selected_vibe` / `event_goal` / `prompt_objective` /
`GTMmatrix`(growth_mode + lifecycle,各含 label+value)/ `preparation_start_date` /
`user_input`(额外要求,可空)/ `content`(用户提供的参考资料,可空)。

产物:`eventplan.json` 写入工作目录,并 merge 进 `plan.json`(键 `eventplan`)。
结构:`{ nodes: { node_1: {section, fields}, ... node_6 }, fields: 合并字段, notes: [...] }`。

## 结果呈现(给用户的样子)—— 不要甩 JSON

工具 stdout 是结构化 JSON,**给用户前要重新组织成一份可读方案**。把 6 个 `node_*.section`
按章节拼起来(每个 `section` 已是 Markdown 正文),组成一份完整文档:

> # 《活动名》活动策划方案
>
> ## 一、活动目标与背景
> {{ nodes.node_1.section }}
>
> ## 二、内容设计(受众 / 流程 / 嘉宾)
> {{ nodes.node_2.section }}
>
> ## 三、场地推荐
> {{ nodes.node_3.section }}
>
> ## 四、关键任务时间线
> {{ nodes.node_4.section 若存在;否则写一句:"时间线请用 loevent-timeline 单独生成" }}
>
> ## 五、合作与赞助
> {{ nodes.node_5.section }}
>
> ## 六、营销推广
> {{ nodes.node_6.section }}

拼完后,把 `notes` 里的降级提示**单独**告诉用户(例如"本次缺 X,建议先跑 Y 再重跑以提质"),
不要把 `fields`(传话字段)原样倒给用户——那是给下游/追溯用的,不是给人读的。

## 时间线(节点 4)

本工具**不生成时间线**——它是独立的 **loevent-timeline**。
- 若 `plan.timeline` 已存在,工具会在结果里带上它(`nodes.node_4`);
- 否则 `notes` 会提示"请用 loevent-timeline 单独生成关键任务时间线"。

## 坑(Pitfalls)
- **缺 vibe 卡(plan.company)**:工具用占位卡降级生成,slogan/互动/嘉宾方向会偏空。
  正确做法:先跑 loevent-company,再让用户选卡。`notes` 会标这条。
- **缺 selected_vibe**:默认取第一张可用卡。建议你先收集用户选择(人机门),别让它默认。
- **缺受众(plan.audience)**:受众相关字段会偏空。先跑 loevent-audience。
- **缺 scene_type/event_scale**:`event_scale` 退化为 `medium`,知识库退化跳过(按 `other`)。
  方案能出,但少了行业/场景化的基准与话术。先跑 loevent-init/loevent-company 可补齐。
- **industry='other'**:行业知识库整体跳过(退化),只用通用 system prompt;节点 6 额外拼平台本地化补强。
