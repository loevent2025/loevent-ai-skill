---
name: loevent-event-strategy
description: 活动策略（Event Strategy）——对主办方做深度调研：挖掘其历史活动 DNA、对标 1~2 个竞品、扫描行业趋势/话题热点/受众痛点，并据此产出三套差异化活动策略方案（品牌传承 / 市场差异化 / 趋势前瞻，各带预算估算）。当用户说"帮我研究这个主办方/分析竞品怎么办活动/给几套活动策略方向/做行业趋势调研/出活动策略"时用。需要先有活动档案与受众画像（先跑 loevent-init，再跑 loevent-audience）。
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

# LoEvent · Event Strategy 活动策略：主办方/竞品/趋势深度调研 + 三套策略方案

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
**缺 `GEMINI_API_KEY` 的处理见 [`references/API-KEY.md`](../references/API-KEY.md)**:先检测、已配置就别再弹;确实缺才弹一次,给「自己改 .env / 直接粘贴」两条路,key 写进**项目根** `.env`(不是沙箱),别甩报错。
**参数 preflight 见 [`references/PREFLIGHT.md`](../references/PREFLIGHT.md)**:`max_competitors`(竞品数)影响调研范围与产出,属**必确认**——把默认值(2)摊给用户、"要改才改"再跑(越多越慢)。`event_goal` / `GTMmatrix` 在本工具**仅留档、调研逻辑不消费 → 沉默**,别问。(受众画像缺失走"先跑 loevent-audience"的串接,不在此弹窗。)

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
   python skill-event-strategy/scripts/run.py
   ```
4. 产物：`company.json` 写入工作目录，核心结论 merge 进 `plan.json`（含 `event_scale`/`scene_type`/`activate_type`，供下游 timeline/poster/social 复用）；结构化结果打印到 stdout。

## 输出结构(company.json 字段速查)
- `strategic_summary`：一段战略总结文案（最该先念给用户的「结论」）。
- `brand_dna` / `competitor` / `trend_forward`：**三套策略卡**，各含 `title`/`slogan`/`location`/`interaction`/`cohost_guest`/`budget`（trend_forward 还有 `url`）。
- `strategic_details.host_insight`：主办方过往 DNA（互动/场地/合作方）。
- `strategic_details.competitors`：竞品对标列表（互动/场地/嘉宾构成 + URL；搜不到的字段为 null）。
- `industry_trends` / `topic_catalyst` / `pain_points`：三段趋势/话题/痛点总结（纯文本）。

## 结果呈现(Presenting Results)— 必读
**绝不要把 `company.json` 的原始 JSON 甩给用户**（但也**不要把调研压成摘要**——用户要靠完整信息做 informed 决策）。
脚本已把完整调研 + 三卡综述落成工作目录里的 **`event_strategy_full.md`**（见输出 JSON 的 `written`）——先把它**指给用户**（"完整版已存 `event_strategy_full.md`"），再在对话里给一份**完整可读版**（Markdown，不是原始 JSON、不删节）。

**呈现顺序（先调研、再三卡、后选卡）：**

> **🏛️ Event Strategy · 主办方调研 + 三套活动策略**
> 📄 完整版：`event_strategy_full.md`
>
> ### 一、全量调研（选卡依据，完整放出，别只给一两句）
> **主办方底色（过往 DNA）**：互动偏好〈host_insight.interaction 逐条〉· 场地〈location〉· 合作方〈cohost〉
> **竞品对标**（〈competitors 数量〉个，逐个完整给）：
> - **〈竞品 title〉**：互动「〈interaction〉」· 场地「〈location〉」· 嘉宾构成「〈guest_composition〉」· 来源〈url〉
> **行业趋势**：〈industry_trends **整段**〉
> **话题引爆点**：〈topic_catalyst **整段**〉
> **受众痛点**：〈pain_points **整段**〉
>
> ### 二、三套策略方向（三张卡各自完整综述，并列对比）
> 1. **品牌传承型** ·「〈brand_dna.title〉」— 〈slogan〉
>    场地：〈location〉· 互动：〈interaction〉· 嘉宾方向：〈cohost_guest〉· **预算：〈budget 完整给，不摘句〉**
> 2. **市场差异化型** ·「〈competitor.title〉」—〈slogan〉…（同上结构，完整）
> 3. **趋势前瞻型** ·「〈trend_forward.title〉」—〈slogan〉…（含 `url` 来源，完整）
>
> ### 三、informed 选卡
> 〈把 strategic_summary（含 AI 推荐及理由）念给用户〉。**用 `AskUserQuestion` 让用户从三套里明确选一张**（selected_vibe）——别替他默认第一张；选定后可据此跑 eventplanner / timeline / poster / social。

要点：
- **先全量调研、再三卡、后选卡**：调研是选卡依据，必须完整放出（趋势/话题/痛点**整段给**，竞品**逐个给**），不得压成摘要；
- 三套方案**并列、各自一段完整综述**，`budget` **完整给**（不再"摘一句量级"）；
- **空字段一律省略**，不显示 `null`；`results_text` 这类原始检索文本可不展示（已在 `.md` 里）；
- 结尾用 **AskUserQuestion** 收 `selected_vibe`，衔接 eventplanner 人机门（**这是必问级人机门，无安全默认**）。

## 易错点(Pitfalls)
- 缺 `event.json`/`host.json` → 脚本会报错提示先跑 loevent-init。
- 缺受众画像 → 脚本会报「缺少 audience.json 或 plan.audience，先跑 loevent-audience」，照做即可。
- 跑得慢/像卡住 → 正常，它在做 20+ 次联网调研；个别趋势卡搜空会自动降级，不算坏。
- 调研质量差/搜不到东西 → 多半是 Key 没联网搜索权限，先 `python engine/doctor.py`。
