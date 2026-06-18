---
name: loevent-guests
description: 为活动嘉宾生成可信、可直接用的嘉宾简介(联网搜索 + 二次事实核查,杜绝同名混淆与编造)。当用户说"帮我写嘉宾简介/介绍这位嘉宾/做嘉宾 bio/查一下这位嘉宾的背景"时用。需要先有活动档案(用 loevent-init 生成)。
version: 0.1.0
metadata:
  hermes:
    tags: [guests, speaker, bio, events, research, grounding]
    category: research
    requires_toolsets: [terminal]
required_environment_variables:
  - name: GEMINI_API_KEY
    prompt: 你的 Google Gemini API Key
    help: 在 https://aistudio.google.com/apikey 申请;本工具靠 Google Search grounding 联网核查,Key 需具备搜索权限
    required_for: 全部功能(联网搜索 + 二次核查 + 成稿)
---

# LoEvent · 嘉宾简介(guests)

输入嘉宾的姓名 / 公司 / 职位,联网做四维搜索(背景、成就、与主题相关性、近半年动态),
再用 Google Search 做一次事实核查与定点修正,最后产出一段**严谨、可直接发布**的嘉宾简介(语言随活动设置)。

## 何时使用(When to Use)
- 用户要给某位活动嘉宾写简介 / bio,或想先了解这位嘉宾的可信背景时。
- 已有一段简介、想**保留原文再联网增补润色**时(传 `guest_profile` 走 enrichment)。
- **前置依赖**:工作目录要有 `event.json`(提供 `theme` 活动主题、`language` 输出语言、`time_start` 用于算"近半年"范围)。没有就先调 **loevent-init** 生成,再回来跑——这种"缺上游就先补"的串接由你(Claude)判断。

## 这个工具靠不靠谱(务必先和用户对齐预期)
- **它会联网**(Google Search grounding),不是凭模型记忆瞎编。
- **两道防线杜绝编造**:① 四维搜索每一维都强制"确认是这家公司的这个人",忽略同名干扰;② 成稿前再用 Google Search 做一次 CHECK/FIX 核查,只改"搜索结果明确证伪"的内容,找不到的标为不确定、绝不当成错误删改。
- **宁缺毋滥**:拿不准的新信息会主动省略;投资角色("主导 / 参与 / 仅机构投资")按证据强度精确措辞,不夸大。
- 所以产出可信度高,但仍建议把关键头衔/事实给用户过一眼。

## 缺东西先弹窗问,别报错也别瞎填(AskUserQuestion)
本 skill 在 Claude Code 里靠**你(Claude)调用 `AskUserQuestion` 工具**来弹窗收集缺失信息——
脚本自己弹不出窗,frontmatter 的 `required_environment_variables` 只在 Hermes/claude.ai 运行时生效,
在 Claude Code 里不触发,所以这里靠 AskUserQuestion 兜底。

- **缺 `GEMINI_API_KEY`**:处理见 [`references/API-KEY.md`](../references/API-KEY.md)——先检测、已配置别再弹;缺了才弹,给「自己改 .env / 直接粘贴」两条路,key 写进**项目根** `.env`(不是沙箱),别甩报错。
- **缺必填业务信息**(嘉宾 name/company/position):也用 AskUserQuestion 问,**一次问清三项**,别零散追问、别自己编。

## 步骤(Procedure)
1. **确认上下文**:工作目录有没有 `event.json`?没有 → 先用 loevent-init 生成。
2. **采集嘉宾输入——用 AskUserQuestion 弹窗问,别瞎填**:
   缺哪项就调 `AskUserQuestion`(三项可一次性问完,各用 Other 让用户填):
   - `guest_name`:嘉宾姓名(**必填**);
   - `guest_company`:所属公司 / 机构(**必填**,用于锁定身份、排除同名);
   - `guest_position`:职位 / 头衔(**必填**);
   - `guest_profile`:已有简介(**可选**)——传了就走 enrichment:**保留全部原文**再联网增补润色;不传则从零联网成稿。
   收齐后写进工作目录的 `guests_input.json`:
   ```json
   {
     "guest_name": "李雷",
     "guest_company": "未来智能 FutureMind",
     "guest_position": "联合创始人 & CTO",
     "guest_profile": ""
   }
   ```
   (也可改用命令行参数:`--name "李雷" --company "未来智能 FutureMind" --position "联合创始人 & CTO"`,可选 `--profile "已有简介…"`。)
3. 运行:
   ```bash
   python skill-guests/scripts/run.py --name "李雷" --company "未来智能 FutureMind" --position "联合创始人 & CTO"
   ```
4. **多位嘉宾就多跑几次**(每次换一组 name/company/position)。结果按嘉宾名累加进 `guests.json`,并 merge 进 `plan.json`(供下游复用);本次结构化结果打印到 stdout。

## 结果呈现(Presenting Results)— 必读
**不要把脚本输出的原始 JSON 直接甩给用户。** 你(Claude)要把它整理成一段干净、可直接用的嘉宾简介小结,例如:

> **🎤 嘉宾简介 · 〈guest_name〉**
> 〈guest_position〉,〈guest_company〉
>
> 〈把 `profile` 字段原样呈现为一段通顺的简介正文——它已经是成稿,别再改写、别加 bullet〉
>
> *(若 `enriched` 为真,可补一句:已在你原有简介基础上联网增补、保留了原文。)*

要点:
- **正文用 `profile` 字段**,它本就是一段可发布的简介;**原样给出**,不要二次改写或拆成要点;
- 顶部用**加粗的姓名 + 一行"职位,公司"**做抬头,清爽;
- 字段为空就略过,**绝不显示 `null` / 原始 JSON / 英文 prompt**;
- 跑完可顺势提示:"还有其他嘉宾要写吗?都写完可以据此排议程 / 出社媒预热文案。"
- **若 `ok` 为 false**(缺必填 / 没出稿):照实把 `error` 用人话转达,并给下一步(补字段、跑 doctor、重试),别报错式甩 traceback。

## 易错点(Pitfalls)
- 缺 `event.json` → 脚本会报错提示先跑 loevent-init,照做即可。
- `guest_company` 别省:它是排除同名、锁定身份的关键;只给名字容易串成另一个人。
- "近半年动态"是基于 `event.json` 的 `time_start` 倒推 6 个月算的——活动时间填错会影响时效判断。
- 缺 `GEMINI_API_KEY` 或 Key 无搜索权限 → 先 `python engine/doctor.py`;grounding 失败时脚本会降级(核查那步跳过、用已得资料成稿),不会崩。
- 这是**单机版**:不写数据库,产物只落在工作目录的 `guests.json` / `plan.json`。
