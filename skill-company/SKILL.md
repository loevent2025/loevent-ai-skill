---
name: loevent-company
description: 对主办方做深度调研——挖掘其历史活动 DNA、对标 1~2 个竞品、扫描行业趋势/话题热点/受众痛点，并据此产出三套差异化活动策略方案（品牌传承 / 市场差异化 / 趋势前瞻，各带预算估算）。当用户说"帮我研究这个主办方/分析竞品怎么办活动/给几套活动策略方向/做行业趋势调研"时用。需要先有活动档案与受众画像（先跑 loevent-init，再跑 loevent-audience）。
version: 0.1.0
metadata:
  hermes:
    tags: [company, competitor, research, strategy, trends, events, grounding]
    category: research
    requires_toolsets: [terminal]
required_environment_variables:
  - name: GEMINI_API_KEY
    prompt: 你的 Google Gemini API Key
    help: 在 https://aistudio.google.com/apikey 申请；本工具全程用 Google Search grounding，需要有联网搜索权限的 Key
    required_for: 全部功能（含 Google Search 联网调研）
---

# LoEvent · 主办方/竞品/趋势深度调研 + 三套策略方案（company）

这是售货机里**最重的一个调研工具**：一次运行会发起约 20+ 次联网 LLM 调用（多组 `asyncio` 并行），
围绕「主办方过往 → 竞品对标 → 行业趋势/话题/痛点 → 三套可落地策略」做一轮完整调研。**请提前告诉用户它会跑几分钟。**

## 何时使用(When to Use)
- 用户想**深挖主办方底色**（过往办过什么活动、互动/场地/嘉宾偏好）；
- 想**对标竞品**（别人怎么办类似活动）找差异化打法；
- 想要**几套可选的活动策略方向**（含调性、场地、互动、嘉宾方向、预算量级）；
- 想要一份**行业趋势 / 话题热点 / 受众痛点**的联网调研。
- **前置依赖（两层）**：工作目录要有
  1. `event.json` + `host.json`（没有 → 先跑 **loevent-init**）；
  2. `audience.json`（或 `plan.json` 里已有 `audience` 字段）——**受众画像是必需输入**，没有 → 先跑 **loevent-audience**。
  这种"缺上游就先补"的串接由你(Claude)判断并提示用户。

## ⚠️ 先讲清两件事
1. **慢 & 费**：约 20+ 次联网调用，会跑一会儿、也更耗 Key 额度。先跟用户打个招呼。
2. **靠 Google Search grounding**：免费档 Key 若没有联网搜索权限，调研质量会打折。先跑 `python engine/doctor.py` 确认。
   单个搜索维度失败会**自动降级跳过**（不让整条管线崩），所以即使个别趋势卡搜空了，主结果照样产出。

## 缺东西先弹窗问,别报错也别瞎填(AskUserQuestion)
在 Claude Code 里,frontmatter 的 `required_environment_variables` **不会**触发原生填 key 弹窗(那是 Hermes/claude.ai 运行时的能力),脚本也弹不出窗。所以**缺 `GEMINI_API_KEY` 时,由你(Claude)调用 `AskUserQuestion`**:header `API Key`、让用户在 **Other** 里粘贴 Key;拿到后写进工作目录 `.env`(`GEMINI_API_KEY=AIza...`,`load_dotenv` 下次跑自动读),再继续。**别把缺 key 的报错直接甩给用户。**
(`max_competitors` / `event_goal` 等均有默认或仅留档,不必弹窗硬问;受众画像缺失走"先跑 loevent-audience"的串接,不在此弹窗。)

## 步骤(Procedure)
1. **确认上下文**：
   - 有没有 `event.json`/`host.json`？没有 → 先 **loevent-init**。
   - 有没有 `audience.json` / `plan.audience`？没有 → 先 **loevent-audience**（本工具读它作为目标受众）。
2. **（可选）确认参数**，写进工作目录的 `company_input.json`：
   ```json
   {
     "max_competitors": 2,
     "event_goal": "product",
     "prompt_objective": "建立 AI 开发者社区心智",
     "GTMmatrix": {
       "growth_mode": {"label": "获取", "value": 40},
       "lifecycle":   {"label": "早期", "value": 30}
     }
   }
   ```
   - `max_competitors`：对标几个竞品（默认 2，建议别超过 3，越多越慢）；
   - `event_goal` / `prompt_objective` / `GTMmatrix`：仅作留档（写进 `company.json._inputs` 供追溯），当前调研逻辑不消费，可省。
   （也可用命令行：`--max-competitors 2 --goal product --objective "…"`。）
3. 运行（会跑几分钟，耐心等）：
   ```bash
   python skill-company/scripts/run.py
   ```
4. 产物：`company.json` 写入工作目录，核心结论 merge 进 `plan.json`（含 `event_scale`/`scene_type`/`activate_type`，供下游 timeline/poster/social 复用）；结构化结果打印到 stdout。

## 输出结构(company.json 字段速查)
- `strategic_summary`：一段战略总结文案（最该先念给用户的「结论」）。
- `brand_dna` / `competitor` / `trend_forward`：**三套策略卡**，各含 `title`/`slogan`/`location`/`interaction`/`cohost_guest`/`budget`（trend_forward 还有 `url`）。
- `strategic_details.host_insight`：主办方过往 DNA（互动/场地/合作方）。
- `strategic_details.competitors`：竞品对标列表（互动/场地/嘉宾构成 + URL；搜不到的字段为 null）。
- `industry_trends` / `topic_catalyst` / `pain_points`：三段趋势/话题/痛点总结（纯文本）。

## 结果呈现(Presenting Results)— 必读
**绝不要把 `company.json` 的原始 JSON 甩给用户。** 这份输出很大且嵌套很深，你(Claude)要**择重整理成可读小结**，例如：

> **🏛️ 主办方调研 · 三套活动策略**
>
> **战略总结**
> 〈把 strategic_summary 用 1~2 句人话点出来〉
>
> **主办方底色（过往 DNA）**
> - 互动偏好：〈host_insight.interaction 逐条，取要点〉
> - 场地偏好：〈host_insight.location〉
> - 常见合作方：〈host_insight.cohost〉
>
> **竞品对标**（〈competitors 数量〉个）
> - **〈竞品 title〉**：互动「〈interaction〉」· 场地「〈location〉」· 嘉宾「〈guest_composition〉」
> - （字段为 null 的省略，不显示 null）
>
> **三套策略方向**（让用户选一个深化）
> 1. **品牌传承型** ·「〈brand_dna.title〉」— 〈slogan〉
>    场地：〈location〉 · 互动：〈interaction〉 · 嘉宾方向：〈cohost_guest〉 · 预算量级：〈budget 摘一句〉
> 2. **市场差异化型** ·「〈competitor.title〉」— 〈slogan〉 …（同上结构）
> 3. **趋势前瞻型** ·「〈trend_forward.title〉」— 〈slogan〉 …（同上结构）
>
> **行业风向**（调研摘要）
> - 行业趋势：〈industry_trends，一两句〉
> - 话题热点：〈topic_catalyst，一两句〉
> - 受众痛点：〈pain_points，一两句〉
>
> 想深化哪一套？我可以据此排时间线 / 出海报 / 写社媒文案。

要点：
- **先给结论**（战略总结 + 三套方案标题/slogan），再给支撑细节；
- 三套方案**并列、各自一段**，每段点出场地/互动/嘉宾/预算，方便用户对比着选；
- **空字段一律省略**，不要显示 `null`；`budget` 是一段联网估算文本，摘一句量级即可，别整段贴；
- `results_text`/`url` 这类原始检索过程**不用展示**；
- 末尾给一句**可执行的下一步建议**（顺势引到 timeline/poster/social）。

## 易错点(Pitfalls)
- 缺 `event.json`/`host.json` → 脚本会报错提示先跑 loevent-init。
- 缺受众画像 → 脚本会报「缺少 audience.json 或 plan.audience，先跑 loevent-audience」，照做即可。
- 跑得慢/像卡住 → 正常，它在做 20+ 次联网调研；个别趋势卡搜空会自动降级，不算坏。
- 调研质量差/搜不到东西 → 多半是 Key 没联网搜索权限，先 `python engine/doctor.py`。
