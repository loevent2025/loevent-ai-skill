---
name: loevent-timeline
description: 为活动生成一份筹备时间线(任务 + 起止日期 + 优先级 P0~P3 + 标签)。当用户说"帮我排筹备计划/出个时间线/倒排期/距活动还有X天该做啥"时用。需要先有活动档案(用 loevent-init 生成 event.json/host.json);业务定位(场景/规模/目标/嘉宾)取自 plan.json,缺省也能出基线。
version: 0.1.0
metadata:
  hermes:
    tags: [timeline, planning, events, project-management, schedule]
    category: planning
    requires_toolsets: [terminal]
required_environment_variables:
  - name: GEMINI_API_KEY
    prompt: 你的 Google Gemini API Key
    help: 在 https://aistudio.google.com/apikey 申请
    required_for: 全部功能
---

# LoEvent · 筹备时间线(timeline)

从活动信息出发,基于场景知识库生成一份**倒排期**:每个筹备任务带起止日期、
优先级(P0~P3)和业务标签(Marketing / Commercial / Venue / General)。
工具会按「筹备开始日 → 活动日」的实际天数,对知识库任务时长做缩放,再交给模型
做精修(改名、按时间松紧增删 P3 任务、补空档、校验排期边界)。

## 何时使用(When to Use)
- 用户要排筹备计划 / 倒排期 / 看「还剩多少天该做什么」。
- **前置依赖**:工作目录要有 `event.json`(取 event_name/theme/活动日期 time_start/language)
  和 `host.json`(取 industry/host_profile)。没有就先调 **loevent-init**——这种"缺上游就先补"由你(Claude)判断。
- 业务定位(场景类型 / 规模 / 目标 / 嘉宾 / 当天流程)取自 `plan.json`;**没有 plan.json 也能跑**,
  会用缺省(场景 `business_conferences`、规模 `medium`)出一份基线时间线。

## 业务字段从哪来(双源,务必理解)
`plan.json` 支持两种形态,工具自动识别:
1. **抽取态**:`plan.json` 里有 `ai_extracted` 字典(loevent-init 从用户原文抽出的)→
   取它的 `scene_type / event_scale / goal / content / guests`。
2. **规划态**:`plan.json` 是一组扁平字段 → 取
   `scene_type / event_scale / eventType / eventTone / organizerProfile / guestInfo /
   eventGoal / shortTermGoals / midTermGoals / longTermGoals / twitterMetrics / eventFlow`。

两种都缺时走缺省。`scene_type` 决定读哪个知识库;`event_scale`(small/medium/large)决定基准筹备天数。

## 缺东西先弹窗问,别报错也别瞎填(AskUserQuestion)
在 Claude Code 里,frontmatter 的 `required_environment_variables` **不会**触发原生填 key 弹窗(那是 Hermes/claude.ai 运行时的能力),脚本也弹不出窗。所以**缺 `GEMINI_API_KEY` 时,由你(Claude)调用 `AskUserQuestion`**:header `API Key`、让用户在 **Other** 里粘贴 Key;拿到后写进工作目录 `.env`(`GEMINI_API_KEY=AIza...`,`load_dotenv` 下次跑自动读),再继续。**别把缺 key 的报错直接甩给用户。**
(`preparation_start_date` 有默认、`prompt` 可选,均不必弹窗硬问;活动日期 `time_start` 缺失属上游 `event.json` 问题,走"先跑 loevent-init"的串接。)

## 步骤(Procedure)
1. **确认上下文**:有没有 `event.json`/`host.json`?没有先跑 **loevent-init**。
   确认 `event.json` 里有 `time_start`(活动日期,`YYYY-MM-DD`)——日期数学全靠它。
2. **采集少量输入(向用户问清,别瞎填)**,写进工作目录的 `timeline_input.json`:
   - `preparation_start_date`:筹备开始日 `YYYY-MM-DD`(默认 `2026-01-21`);
   - `user_tasks`:用户**必须保留、不可删**的自定义任务(可选,数组);
   - `prompt`:额外说明(如"嘉宾以 VC 为主,提前锁场地")。
   ```json
   {
     "preparation_start_date": "2026-01-21",
     "user_tasks": [
       {"task_name": "CEO 主题演讲彩排", "tag": "General", "startDate": "2026-03-10", "endDate": "2026-03-11", "priority": "P0"}
     ],
     "prompt": "嘉宾以一线 VC 为主,场地需尽早锁定"
   }
   ```
   (也可用命令行:`--start 2026-01-21 --prompt "…"`。)
3. 运行:
   ```bash
   python skill-timeline/scripts/run.py
   ```
4. 产物:`timeline.json` 写入工作目录,并 merge 进 `plan.json`(供下游复用);结构化结果打印到 stdout。

## 结果呈现(Presenting Results)— 必读
**不要把脚本输出的原始 JSON 直接甩给用户。** 你(Claude)要把它整理成清晰、可执行的排期视图。建议:

> **🗓️ 筹备时间线（〈event_name〉)**
> 筹备期:**〈start_date〉 → 〈event_date 前一天〉**(场景 〈scene_type〉 · 规模 〈event_scale〉,共 N 个任务)
>
> **🔴 P0 关键里程碑(不可省)**
> - `〈startDate〉–〈endDate〉` **〈task_name〉** · 〈tag〉
> - …
>
> **🟠 P1 核心 / 🟡 P2 重要 / ⚪ P3 增值**
> - 按优先级或按周分组,逐条列「日期 + 任务名 + 标签」
>
> **小结**:开局两周先抓 〈最早的 P0 群〉;志愿者/排班/彩排集中在活动前一周;关键路径上注意 〈某依赖〉。

要点:
- **按优先级(P0→P3)或按周/阶段分组**,每条给「起止日期 + 任务名 + 标签」,日期对齐好读;
- 用 emoji/加粗区分优先级,P0 醒目;**用户自定义任务(user_tasks)要标注出来**,提示它们被保留;
- 末尾给一句**可执行小结**:点出最早要启动的事、活动前一周的硬约束(志愿者/彩排)、和潜在风险;
- 字段为空(如某些 tag/优先级没有任务)就**省略**,不显示 `null` / 空段;
- **别贴整段 JSON、别贴 multipliers/meta 这类内部字段**;
- 跑完可顺势问:"要不要据此出预算 / 写招募文案 / 排嘉宾邀约?"

## 易错点(Pitfalls)
- 缺 `event.json`/`host.json` → 脚本报错提示先跑 loevent-init,照做即可。
- `event.json.time_start` 必须是活动日期且**晚于**筹备开始日,否则脚本会报"活动日期必须晚于开始日"。
- `host.json.industry` 要能被 `industry_map` 识别(如 `AI & Technology` / `WEB 3` / `General`);
  识别不了会报错提示——向用户确认行业后改 `host.json`。
- `scene_type` 必须是知识库里有的场景(business_conferences / hackathons / cocktail / demo_days /
  developer_meetups / technical_workshops / community_day / crossover / large_exhibitions);
  填了不存在的场景脚本会列出可用值。
- 缺 `GEMINI_API_KEY` → 先 `python engine/doctor.py`。
