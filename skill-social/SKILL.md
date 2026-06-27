---
name: loevent-social
description: 为活动生成社交媒体文案(小红书 / X / 社群三选一,可选长度与语气)。当用户说"帮我写小红书/X/社群推文、出条宣传文案、写活动预热/倒计时帖"时用。需要先有活动档案(用 loevent-init 生成);可选地用 inspiration.json(行业趋势/热点/痛点)增强。
version: 0.1.0
metadata:
  hermes:
    tags: [social, copywriting, content, events, marketing, xiaohongshu, twitter]
    category: content-creation
    requires_toolsets: [terminal]
required_environment_variables:
  - name: GEMINI_API_KEY
    prompt: 你的 Google Gemini API Key
    help: 在 https://aistudio.google.com/apikey 申请(纯文本生成,免费档即可)
    required_for: 全部功能
---

# LoEvent · 社交媒体文案(social)

按平台 + 长度 + 语气,从活动信息生成一条可直接发布的社交媒体文案。
内置 540 篇分行业/场景/激活方式的知识库,自动按活动匹配对应写作规范。

## 何时使用(When to Use)
- 用户想要一条小红书 / X(推特)/ 社群(微信群、Discord 公告)文案时。
- 想做不同阶段的推文:预热(warmup)、正式宣发(active)、倒计时(countdown)、最后召集(lastcall)。
- **前置依赖**:工作目录要有 `event.json` 和 `host.json`(没有就先调 **loevent-init**)。
  - 强烈建议也先有 `plan.json`(里面带 guests / eventGoal / eventFlow / targetAudience,
    由 loevent 的活动策划/受众类工具产出)——这样文案能引用嘉宾、议程、目标,质量明显更高。
  - 可选 `inspiration.json`(行业趋势 / 热点 / 痛点)——配合 `inspiration_source` 让文案更有"钩子"。

## 平台与参数(三个必填项,别瞎填)
- `platform`(**必填**):`xiaohongshu`(小红书,带标题)/ `x`(推特,简短)/ `community`(社群公告)。
- `length`(**必填**):`short` / `medium` / `long`。
- `tone`(**必填**):`professional_tone`(专业)/ `friendly_tone`(亲切)/ `humorous_tone`(幽默)/ `educational_tone`(科普)。

可选(向用户问清需要哪些,不需要就略过):
- `stage`:`warmup` / `active`(默认)/ `countdown` / `lastcall` —— 影响嘉宾、议程怎么呈现。
- `content_focus`:主焦点,`guest_profile`(嘉宾)/ `event_agenda`(议程)/ `event_purpose`(活动目的)/ `basic_information`。
- `content`:次焦点(可多个),取值同上。
- `inspiration_source`:`industry_trend` / `hot_topic` / `painpoint`(需要 `inspiration.json` 里有对应字段才生效)。
- **落地信息(CTA 用)**:`registration_method`(报名方式)、`detail_location_*`(国/市/街/楼层)、`ticket` + `ticket_price`(是否售票 + 票价)。文案的行动号召(CTA)靠这几项才写得出"在哪、怎么报名、多少钱";缺了只能泛喊"快来"。

## 缺东西先弹窗问,别报错也别瞎填(AskUserQuestion)
在 Claude Code 里,frontmatter 的 `required_environment_variables` **不会**触发原生填 key 弹窗(那是 Hermes/claude.ai 运行时的能力),脚本也弹不出窗。需要时由你(Claude)调用 `AskUserQuestion`:
- **缺 `GEMINI_API_KEY`**:处理见 [`references/API-KEY.md`](../references/API-KEY.md)——先检测、已配置别再弹;缺了才弹,给「自己改 .env / 直接粘贴」两条路,key 写进**项目根** `.env`(不是沙箱),别甩报错。
- **缺 `platform`**(必填,且"猜哪个平台"必错,无安全默认):调 AskUserQuestion,header `平台`,选项 `小红书 xiaohongshu` / `X(推特)` / `社群 community` 让用户单选。`length`(默认 medium)/ `tone`(默认 professional)有合理默认,**不必弹窗硬问**——可一并放进同一次 AskUserQuestion 让用户"要改才改",不改就走默认,别因为它们打断。
- **落地信息**(`registration_method` / `detail_location_*` / `ticket` + `ticket_price`):当 `stage` 是 `active` / `countdown` / `lastcall` 这类带行动号召的阶段时,**主动**用 AskUserQuestion 问一次"怎么报名 / 详细地址 / 是否售票 + 票价"(可合进同一次弹窗,header 如 `报名方式`、`详细地址`、`票价`)——问到 CTA 才落得了地。用户说"没有 / 暂不公开"就留空,文案走"私信 / 扫码了解"之类兜底,别瞎编地址票价。`warmup`(纯预热)阶段不必问,留空即可。

## 步骤(Procedure)
1. **确认上下文**:工作目录有没有 `event.json` / `host.json`?没有 → 先跑 loevent-init。
   有没有 `plan.json` / `inspiration.json`?没有也能跑,但提醒用户文案会更"泛"。
2. **和用户敲定三个必填项**(platform / length / tone),再问要不要带 stage / 焦点 / 灵感来源。
   **若是 `active` / `countdown` / `lastcall` 等带 CTA 的阶段**,顺带把落地信息(报名方式 / 详细地址 / 是否售票 + 票价)问齐,否则 CTA 落不了地。
   把它们写进工作目录的 `social_input.json`:
   ```json
   {
     "platform": "xiaohongshu",
     "length": "medium",
     "tone": "professional_tone",
     "stage": "active",
     "content_focus": "guest_profile",
     "content": ["event_agenda"],
     "inspiration_source": ["industry_trend", "painpoint"],
     "registration_method": ["官网报名", "扫码进群"],
     "detail_location_city": "上海",
     "detail_location_street": "徐汇西岸",
     "ticket": false,
     "ticket_price": ""
   }
   ```
   (也可用命令行:`--platform xiaohongshu --length medium --tone professional_tone --stage active --content-focus guest_profile --content event_agenda --inspiration-source industry_trend`;`--content` / `--inspiration-source` / `--registration-method` 可重复。)
3. 运行:
   ```bash
   python skill-social/scripts/run.py
   ```
4. 产物:`social.json`(含 content / contentLength / content_tones,小红书还含 title)写入工作目录,
   并 merge 进 `plan.json`;结构化结果打印到 stdout。

## 结果呈现(Presenting Results)— 必读
**不要把脚本输出的原始 JSON 直接甩给用户。** 你(Claude)要把它整理成"可以直接复制去发"的样子:

> **📱 小红书文案已生成 ✅**(平台/长度/语气一行小标注:`xiaohongshu · medium · professional_tone`)
>
> **标题**:〈title,仅小红书有;其它平台略过这行〉
>
> ---
> 〈把 `social.content` **原样、保留换行**地贴出来 —— 这是要发布的正文,不要改写、不要再加工〉
> ---
>
> 这条围绕〈一句话点出主打的焦点,如"嘉宾阵容 + 行业趋势钩子"〉来写。
> 想换平台 / 调长度 / 改语气(更亲切?更幽默?)或做"倒计时"版,告诉我重出。

要点:
- **正文 `content` 必须原样呈现并保留换行**(脚本已做过换行精修,别再压成一行);
- 小红书有 `title` 就单独加粗显示,**其它平台没有 title 就不要显示这行**;
- 用一行小标注交代 平台 · 长度 · 语气,方便用户核对;
- **空字段一律省略**,不显示 `null` / `""`;
- 末尾给"可继续操作"的提示(换平台 / 改语气 / 出倒计时版),让对话往下走;
- 如果脚本返回 `ok: false`,把 `error` 翻成人话 + 照 `hint` 引导(多半是缺 `GEMINI_API_KEY` 或缺 `event.json`),**不要甩 traceback**。

## 易错点(Pitfalls)
- 缺 `event.json` / `host.json` → 脚本会报错提示先跑 loevent-init,照做即可。
- `platform` / `length` / `tone` 是必填,缺了会落到默认(xiaohongshu / medium / professional_tone)——
  **先跟用户确认再跑**,别默认。
- **CTA 落不了地**:`active` / `countdown` / `lastcall` 阶段若没给 `registration_method` / `detail_location_*` / 票价,行动号召只能泛喊"快来报名",发出去用户不知道在哪、怎么报名。这几项虽非必填,但带 CTA 的阶段强烈建议先问齐(见上「落地信息」);用户确实没有再留空走兜底。
- `inspiration_source` 选了但工作目录没有 `inspiration.json`(或里面没对应字段)→ 该来源会被静默忽略,文案照常出,只是少了那层钩子。
- 知识库只覆盖 `web3` / `ai_commercial` 两类行业;`host.industry` 落到 `other` 时不注入领域知识库(文案仍会生成,只是更通用)。
- 缺 `GEMINI_API_KEY` 或网络/grounding 异常 → 脚本会降级返回 `ok: false` + hint,先 `python engine/doctor.py`。
