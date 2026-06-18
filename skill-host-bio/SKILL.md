---
name: loevent-host-bio
description: 调研并润色主办方(公司/组织)简介——读官网 + 联网搜索,产出带【公司简介/产品定位/核心功能/用户规模/技术核心/竞争对手】六维的规范公司简介和标准公司名。当用户说"帮我写主办方简介/介绍下这家公司/补全 host 档案/这家办活动的公司是做什么的"时用。需要官网 URL;联网调研需要有 grounding 权限的 Gemini Key。
version: 0.1.0
metadata:
  hermes:
    tags: [host, company, profile, research, events, grounding]
    category: research
    requires_toolsets: [terminal]
required_environment_variables:
  - name: GEMINI_API_KEY
    prompt: 你的 Google Gemini API Key
    help: 在 https://aistudio.google.com/apikey 申请;联网调研(Google Search / URL context)需要相应权限,免费档可能受限
    required_for: 全部功能(两步都是文本调用,但第一步要联网读官网)
---

# LoEvent · 主办方简介调研(host-bio)

给定主办方官网,联网调研这家公司,产出一份**结构化、可直接用**的公司简介(六个维度)和**规范公司名**,
并回写进本地 `host.json`,供下游(受众画像 / 海报 / 社媒文案 / 预算)复用。

## 何时使用(When to Use)
- 用户给了主办方官网、想要一份正经的公司简介 / host 档案时。
- 下游工具(audience / poster / socialpost…)需要 `host.json` 里的 `host_name` 和 `host_profile`,但目前缺失或太粗糙时——本工具就是来补全它的。
- **前置依赖(轻)**:本工具**不强依赖** `event.json`;只需要一个**官网 URL**。
  如果工作目录已有 `host.json`(loevent-init 生成),会自动读它的 `industry / host_name / self_description` 当缺省,但没有也能跑。

## ⚠️ 先讲清一件事(联网与降级)
- 第一步要**联网读官网 + 搜公司信息**(URL context / Google Search)。若当前 Key 没有 grounding 权限、官网打不开,或结构化解析失败,
  本工具会**降级返回原因而不是崩**(输出 `degraded: true`)。这时**先跑 `python engine/doctor.py`** 看权限,再按需换 `--website` 或补 `--org`/`--self-description` 重试。

## 缺东西先弹窗问,别报错也别瞎填(AskUserQuestion)
在 Claude Code 里,frontmatter 的 `required_environment_variables` **不会**触发原生填 key 弹窗(那是 Hermes/claude.ai 运行时的能力),脚本也弹不出窗。需要时由你(Claude)调用 `AskUserQuestion`:
- **缺 `GEMINI_API_KEY`**:处理见 [`references/API-KEY.md`](../references/API-KEY.md)——先检测、已配置别再弹;缺了才弹,给「自己改 .env / 直接粘贴」两条路,key 写进**项目根** `.env`(不是沙箱),别甩报错。
- **缺主办方官网 `website`**(本工具必填、无默认、上游档案里也没有):调 AskUserQuestion 让用户贴官网链接(用 Other 自由填),**别瞎编一个 URL**。`org` / `industry` / `self_description` 是可选消歧项,不必弹窗硬问。

## 步骤(Procedure)
1. **拿到官网 URL(必须)**:向用户要主办方官网链接;没有 URL 没法调研,先问清。
2. **(可选)补充消歧信息**,提升准确度——尤其当公司有多条产品线/子品牌时:
   - `org`:公司/组织正式名;
   - `industry`:行业(如 `AI & Technology` / `WEB 3` / `other`);
   - `self_description`:一句话自述(帮模型锁定研究对象)。
   把这些写进工作目录的 `host_bio_input.json`:
   ```json
   {
     "host_website": "https://acme.ai",
     "organization_name": "Acme AI",
     "industry": "AI & Technology",
     "language": "中文",
     "self_description": "面向开发者的垂直 AI 基础设施"
   }
   ```
   (也可用命令行:`--website https://acme.ai --org "Acme AI" --industry "AI & Technology" --language 中文 --self-description "…"`。)
3. 运行:
   ```bash
   python skill-host-bio/scripts/run.py
   ```
4. 产物:`host.json` 被**回写** `host_name` / `host_profile`(以及 `industry`/`host_website`),并 merge 进 `plan.json`;
   完整结构化结果写入 `host_bio.json` 并打印到 stdout。

## 它产出什么(Output)
- `host_name`:从调研数据里识别出的**规范公司/组织名**;
- `host_profile`:一段带六个【label】的**公司简介**,顺序固定:
  **【公司简介】→【产品定位】→【核心功能】→【用户规模】→【技术核心】→【竞争对手】**
  (英文语境则是 【Overview】/【Product Positioning】… 同序)。脚本已自动给【】标记排好换行。

## 结果呈现(Presenting Results)— 必读
**不要把脚本输出的原始 JSON 直接甩给用户。** 你(Claude)要把 `host_profile` 拆成清爽的分段,例如:

> **🏢 〈host_name〉· 主办方简介**
>
> - **公司简介**:〈【公司简介】内容〉
> - **产品定位**:〈【产品定位】内容〉
> - **核心功能**:〈【核心功能】内容〉
> - **用户规模**:〈【用户规模】内容〉
> - **技术核心**:〈【技术核心】内容〉
> - **竞争对手**:〈【竞争对手】内容〉
>
> 一句话总结:〈用一句话点出这家公司是做什么的、在行业里的位置〉。已写入 `host.json`,下游工具可直接用。

要点:
- **按六个维度分点**,每点**加粗维度名 + 内容**,把 `host_profile` 里的【label】解析成对应小标题;
- 顶部先给**公司名**;
- 末尾给**一句话定位总结**(帮用户快速抓住"这家公司是谁");
- **某维度内容是 "N/A" / 为空就直接略过那一行**,不要显示 `null` 或空【label】;
- **降级时**(`degraded: true`):别甩 traceback——用中文说清"联网调研没成功",给出 `reason`/`hint`,
  建议用户:① 跑 `python engine/doctor.py` 看 Key 权限;② 确认官网可访问;③ 补 `--org`/`--self-description` 重试;
- 跑完可顺势提示:"主办方档案补好了,要不要据此做受众画像 / 出海报 / 写社媒文案?"

## 易错点(Pitfalls)
- **缺 `host_website` → 脚本直接报错要 URL**,先向用户要官网链接,别瞎编一个。
- 公司有多产品线时,**务必传 `--org`/`--self-description`**,否则调研可能把子品牌/竞品的数据混进来(prompt 里有反混淆机制,但喂准信息更稳)。
- `language` 决定输出语言和 `host_name` 语言;默认中文,英文场合传 `--language English`。
- 联网失败 ≠ 坏了,多是 Key 没 grounding 权限或官网打不开 → 先 `python engine/doctor.py`,再按降级话术跟用户讲。
- 缺 `GEMINI_API_KEY` → 先 `python engine/doctor.py`。
