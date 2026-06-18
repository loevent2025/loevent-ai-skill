---
name: loevent-poster
description: 为活动生成宣传海报图(按选定视觉风格)。当用户说"做张海报/出个活动海报/生成宣传图"时用。需要先有活动档案(用 loevent-init 生成);生成图片需要计费档的 Gemini Key。
version: 0.1.0
metadata:
  hermes:
    tags: [poster, design, image, events, marketing]
    category: content-creation
    requires_toolsets: [terminal]
required_environment_variables:
  - name: GEMINI_API_KEY
    prompt: 你的 Google Gemini API Key
    help: 在 https://aistudio.google.com/apikey 申请;**生成图片需要计费档**(免费档大概率只能出 prompt、出不了图)
    required_for: 图像生成(组 prompt 不需要计费档)
---

# LoEvent · 活动海报生成(poster)

按选定风格,从活动信息生成一张宣传海报。

## 何时使用(When to Use)
- 用户想要一张活动海报 / 宣传图时。
- **前置依赖**:工作目录要有 `event.json` 和 `host.json`(没有就先调 loevent-init)。

## ⚠️ 先讲清两件事(降级与计费,务必先告诉用户)
1. **生成图片需要"计费档"的 Gemini Key**(模型 `gemini-3-pro-image`)。免费档 Key 通常没有图像权限。
   **先跑 `python engine/doctor.py`** 看图像档是否可用。
2. **若图像档不可用,本工具会自动降级**:仍然产出并保存「生成指令(generation_prompt)」,只是不出图。
   这不是报错——你(Claude)要把 prompt 给用户,让他拿去任何能生图的工具用。
3. 单机版**不含**海报精修(去文字 / OCR 版面分析)——那条链路依赖 Google Cloud Vision 服务账号,
   不是一个 api-key 能搞定的,v1 不做。

## 缺东西先弹窗问,别报错也别瞎填(AskUserQuestion)
本 skill 在 Claude Code 里靠**你(Claude)调用 `AskUserQuestion` 工具**弹窗收集缺失信息——
脚本自己弹不出窗,frontmatter 的 `required_environment_variables` 只在 Hermes/claude.ai 运行时生效,
在 Claude Code 里不触发,所以这里靠 AskUserQuestion 兜底。

- **缺 `GEMINI_API_KEY`**(环境没设、或脚本报缺 key):别甩报错。调用 AskUserQuestion:
  - header `API Key`;question:`还没配置 Gemini API Key,请贴入你的 Key(出图还需计费档)`;
  - 选项给「我去申请(https://aistudio.google.com/apikey)」+ 让用户在 **Other** 里粘贴 Key。
  - 拿到后写进工作目录 `.env`(`GEMINI_API_KEY=AIza...`),`load_dotenv` 下次跑自动读;再继续。
- **缺风格/规格**:用下面步骤 2 的 AskUserQuestion 弹窗问,别默认、别瞎填。

## 步骤(Procedure)
1. **确认上下文**:有没有 `event.json`/`host.json`?没有先跑 loevent-init。
2. **用 AskUserQuestion 弹窗和用户确定风格与规格**(别瞎填、别默认):
   - `style`:调 `AskUserQuestion`,header `海报风格`,从下方风格清单挑 4~6 个做选项
     (如 `minimalist`/`cyberpunk`/`techgradient`/`glassmorphism` …),设 `multiSelect: true` 让用户可多选叠加 1~2 个;
   - `ratio`:再来一题,选项 `1:1` / `9:16`(竖屏故事) / `16:9`(横屏);
   - `resolution`:选项 `1K` / `2K` / `4K`;
   - 可选 `prompt`(额外方向,如"突出开发者社区氛围")、`color`(主色 hex)——让用户在 Other 里填,不填就略过。
   (ratio/resolution/style 可合并在一次 AskUserQuestion 的多道题里问完,减少打断。)
   收齐后写进工作目录的 `poster_input.json`:
   ```json
   {
     "poster_style": ["minimalist"],
     "ratio": "9:16",
     "resolution": "2K",
     "prompt": "强调 AI 开发者社区、科技感",
     "event_color": "#1a1a2e"
   }
   ```
   (也可用命令行:`--style minimalist --ratio 9:16 --resolution 2K --prompt "…" --color "#1a1a2e"`;`--style` 可重复。)
3. 运行:
   ```bash
   python skill-poster/scripts/run.py
   ```
4. 产物:`poster_<n>.png`(出图成功时)+ `poster.json`(含 generation_prompt 与图像状态),写入工作目录。

## 可选风格清单(style)
`minimalist`(极简)、`cyberpunk`(赛博朋克)、`techgradient`(科技渐变)、`glassmorphism`(玻璃拟态)、
`liquidglass`(液态玻璃)、`midnightneon`(午夜霓虹)、`neonlounge`(霓虹)、`synthwave` / `retrowave` / `vaporwave`(合成波/蒸汽波)、
`gridlayout`(网格)、`geometricgraphic`(几何)、`lowpoly`(低多边形)、`isometricfantasy`(等距奇幻)、
`3drender`(3D 渲染)、`generativeart`(生成艺术)、`dataflow`(数据流)、`matrixflow`、`glowpixel`、`pixelart`、`popart`、
`blackgold`(黑金)、`purplemystic`、`moonlightfantasy`、`spacetech`、`citysilhouette`、`gradientblur`、`holographicglow`、`softshimmer`、`pastelcyberpunk`、`glitchart`、`algorithmicdesign`、`photocomposite`、`osaesthetics`、`keyboardview`、`pixelrock`、`chromaticshards`、`retroskeuomorphic`。
(不确定就向用户描述几种、让他选;别默认。)

## 结果呈现(Presenting Results)— 必读
**不要把脚本的原始 JSON 甩给用户。** 分两种情况整理:

**A. 出图成功**(`image.saved_to` 有值):
> **🎨 海报已生成 ✅**
> - 风格:〈style〉  ·  比例:〈ratio〉  ·  分辨率:〈resolution〉
> - 文件:`〈image.saved_to〉`(已存到本地,可直接打开查看)
> - 设计要点:用一两句**人话**概括 generation_poster_prompt 的核心(主视觉/配色/氛围),不要贴整段英文 prompt。
>
> 需要换风格、改比例或调主色,告诉我重出。

**B. 降级未出图**(`image.degraded` 为真):
> **⚠️ 当前 Key 没有图像生成权限,海报图没出成**,但我已经生成了完整的「海报生成指令」并存好了。
> 你可以:① 申请计费档的 Gemini Key 后重试;② 把这段指令拿到任意能生图的工具直接用。
> (然后把 generation_poster_prompt 贴出来给用户,并附一句中文说明它描述了什么。)

要点:成功就给**文件路径 + 一句话设计概括**;降级就**讲清原因 + 把 prompt 交付给用户**,绝不报错式甩 traceback。

## 易错点(Pitfalls)
- 缺 `event.json`/`host.json` → 先 loevent-init。
- 出不了图≠坏了,大多是 Key 没图像档 → 先 `python engine/doctor.py`,再按降级话术跟用户讲。
- 参考图(`--reference 本地图片`)是可选高级用法,需要装 `Pillow`;不传则用风格知识库。
