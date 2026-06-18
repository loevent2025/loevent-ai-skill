---
name: loevent-trends
description: 为活动做实时行业调研——行业趋势洞察 / 话题引爆点 / 受众痛点共鸣三类卡片(联网搜索 + 二次核查)。当用户问"现在这个行业有什么趋势/最近有什么热点能蹭/我的受众在纠结什么/帮我找活动选题素材"时用。需要先有活动档案(用 loevent-init 生成);最好先跑 loevent-audience 拿到受众画像,痛点调研会更准。
version: 0.1.0
metadata:
  hermes:
    tags: [trends, research, market, audience, events, marketing]
    category: research
    requires_toolsets: [terminal]
required_environment_variables:
  - name: GEMINI_API_KEY
    prompt: 你的 Google Gemini API Key
    help: 在 https://aistudio.google.com/apikey 申请;本工具靠联网搜索(grounding),普通文本档 Key 即可,不需要计费档
    required_for: 全部功能(联网搜索 + 综合)
---

# LoEvent · 实时行业调研(trends)

围绕活动主题做三类实时调研,每类都"先联网搜、再自查核实、最后综合成卡":
- **行业趋势洞察(trends)**:讨论热度 / 主流观点 / 趋势变化 —— 提供社会证明,帮你把握行业脉搏。
- **话题引爆点(catalyst)**:重大新闻 / 政策动态 / 企业动态 / 技术突破 —— 找近 30 天能蹭的热点选题。
- **受众痛点共鸣(pain)**:担忧顾虑 / 高频疑问 / 真实声音 —— 击中目标人群的情感共鸣点。

## 何时使用(When to Use)
- 用户想了解行业最新趋势、找活动选题/内容素材、或洞察受众真实痛点时。
- **前置依赖**:
  - 工作目录要有 `event.json` 和 `host.json`(没有就先调 **loevent-init**)。
  - **强烈建议先跑 loevent-audience**:它会把受众画像 merge 进 `plan.json`,本工具的"受众痛点"维度会读它、调研更精准。没有也能跑(退化为按主题搜),但效果打折——这种"缺上游先补"的串接由你(Claude)判断。

## ⚠️ 先讲清一件事(联网与降级)
- 本工具**靠联网搜索(Google Search grounding)**取实时信息,并对搜到的内容做**二次事实核查 + 修正**(NO_ISSUES 就放行,有问题才联网改)。
- 普通文本档 Key 就能跑,**不需要计费档**。
- **某个维度搜不到 / 网络抖动会自动降级**:那张卡返回空、记进 `degraded`,其它卡照常出——不是整体报错。出现 `degraded` 时告诉用户"这块这次没搜到,可换个角度或稍后重试",别当成崩溃。

## 缺东西先弹窗问,别报错也别瞎填(AskUserQuestion)
**缺 `GEMINI_API_KEY` 的处理见 [`references/API-KEY.md`](../references/API-KEY.md)**:先检测、已配置就别再弹;确实缺才弹一次,给「自己改 .env / 直接粘贴」两条路,key 写进**项目根** `.env`(不是沙箱),别甩报错。
(`dimension` 默认 `all`、`prompt` 可选,均不必弹窗硬问;想缩窄维度时在下面步骤 2 顺带问即可。)

## 步骤(Procedure)
1. **确认上下文**:有没有 `event.json`/`host.json`?没有先跑 loevent-init。再看 `plan.json` 里有没有 `audience`(loevent-audience 的产物);没有就建议先跑它,尤其当用户要的是"受众痛点"。
2. **和用户确认要跑哪一类**(别全默认):
   - 只想看行业大势 → `trends`;
   - 想找能蹭的近期热点选题 → `catalyst`;
   - 想懂受众在纠结什么 → `pain`;
   - 都要 → `all`(默认)。
   可选 `prompt` 给个额外方向(如"侧重出海""聚焦中小企业开发者")。可写进工作目录的 `trends_input.json`:
   ```json
   {
     "dimension": "all",
     "prompt": "侧重 AI 应用开发者关心的落地与成本话题"
   }
   ```
   (也可用命令行:`--dimension catalyst --prompt "侧重出海"`。)
3. 运行(默认三类全跑;耗时较长,因为每类要并行多轮联网搜索 + 核查):
   ```bash
   python skill-trends/scripts/run.py                    # 全跑
   python skill-trends/scripts/run.py --dimension pain   # 只跑受众痛点
   python skill-trends/scripts/run.py --dimension trends --prompt "侧重出海"
   ```
4. 产物 `inspiration.json` 写入工作目录,各卡的 `summary`/`url` 同步 merge 进 `plan.json`(供下游"趋势前瞻"方案等复用);结构化结果打印到 stdout。

## 结果呈现(Presenting Results)— 必读
**不要把脚本输出的原始 JSON 直接甩给用户。** 你(Claude)要按跑了哪几类,分块整理成清晰可读的小结。每类的 `summary` 是核心,`url` 是出处——**有 url 才附来源,空字段直接省略,不显示 `null`**。例如:

> **📈 行业趋势洞察**(trends)
> - **核心动向**:〈用一两句概括 industry_trends.summary,讲人话〉
> - **讨论热度 / 主流观点 / 趋势变化**:〈各拎 1-2 个最有信息量的点,加粗小标题分块〉
> - 来源:〈若 url 非空,列 1-3 条最权威的链接;否则整行省略〉
>
> **🔥 话题引爆点**(catalyst)
> - 近 30 天值得蹭的热点:〈从 topic_catalyst.summary 提炼 2-3 个选题角度〉
> - 来源:〈同上,空则省略〉
>
> **💔 受众痛点共鸣**(pain)
> - 受众最在意的:〈从 audience_pain_points.summary 提炼核心痛点 + 情绪〉
> - 一句可直接用的共鸣切入:〈给一个能写进文案/开场的钩子〉
>
> 一句话建议:据此,这场活动的内容/选题可优先围绕「〈最强的那个趋势或痛点〉」展开。

要点:
- **按维度分块**,每块先给核心结论、再点 1-2 个细节;
- `summary` 用人话转述,不要逐字贴整段;`url` 当作来源附在块尾,**空就省略**;
- 末尾给一句**可执行建议**(把调研落到选题/内容/嘉宾决策上);
- 若有维度进了 `degraded`,**坦诚说明这块这次没搜到**,并提议换角度或稍后重试,不要硬编;
- 跑完可顺势提示:"要不要据此出社媒文案 / 排时间线 / 定海报方向?"

## 易错点(Pitfalls)
- 缺 `event.json`/`host.json` → 脚本会报错提示先跑 loevent-init,照做即可。
- 没跑 loevent-audience → "受众痛点"维度会退化为只按主题搜;要更准就先补 audience。
- `event.time_start` 缺失 → 行业趋势/话题引爆点的"近 N 月"时间窗会退化为"近期",问题不大但提一句。
- 出现 `degraded`≠坏了,多是某维度联网没搜到或网络抖动 → 按降级话术跟用户讲,可换 `--prompt` 角度重试。
- 缺 `GEMINI_API_KEY` → 先 `python engine/doctor.py`。
