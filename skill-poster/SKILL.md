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
3. **文字可编辑(可选)**:出图后可把文字做成可改的——定位文字 → `gemini-2.5-flash-image` 消字 → 系统字体渲染回去(见下文「文字可编辑」)。
   **定位有两档,自动择优**:配了 GCV 服务账号(`GOOGLE_APPLICATION_CREDENTIALS`,独立于 `GEMINI_API_KEY`)→ 用它**精确**取框;**没配也能用**→ 降级到"看图估位置 + HTML 编辑器里微调"。两种都不影响普通出图。

## 缺东西先弹窗问,别报错也别瞎填(AskUserQuestion)
本 skill 在 Claude Code 里靠**你(Claude)调用 `AskUserQuestion` 工具**弹窗收集缺失信息——
脚本自己弹不出窗,frontmatter 的 `required_environment_variables` 只在 Hermes/claude.ai 运行时生效,
在 Claude Code 里不触发,所以这里靠 AskUserQuestion 兜底。

- **缺 `GEMINI_API_KEY`**:处理见 [`references/API-KEY.md`](../references/API-KEY.md)——先检测、已配置别再弹;缺了才弹,给「自己改 .env / 直接粘贴」两条路,key 写进**项目根** `.env`(不是沙箱),别甩报错。(出图还需**计费档** Key。)
- **缺风格/规格**:用下面步骤 2 的 AskUserQuestion 弹窗问,别默认、别瞎填。
**海报会印在对外成品上的字段,出图前按 [`references/PREFLIGHT.md`](../references/PREFLIGHT.md) 先 preflight:**
- **活动开始时间 —— 必问**(无安全默认、会印上对外海报):海报底部会印 `event.time_start`。若它**只有日期、没有具体钟点**(抽取时常被补成 `00:00`),**别让海报印出 `… 00:00` 这种半夜占位**——出图前用 AskUserQuestion 问用户具体开始时间;用户暂时没定 → **只印日期**。(脚本已会自动剥掉占位的 `00:00`,这里再问一道是给用户补真实时间的机会。)
- **主标题 / 副标题 —— 必确认(建议默认·可改)**:海报主视觉文字默认从 `event_name` / `theme` 衍生。出图前把这个草稿**摊给用户瞄一眼、"要改才改"**再出——避免主/副标题重复、过长或不达意就直接印上对外海报。

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

## 文字可编辑(可选,出图后)—— 把"烤进像素的字"变成可改的

图像模型把文字烤进像素,容易错字、混语言、不可改。需要文字可控/可改时,出图后走这条
(脚本 `skill-poster/scripts/poster_text.py`;中文渲染走**系统字体**,不打包不下载):

**定位文字有两档,自动择优**(消字/渲染两档通用):
- **优先·精确(GCV)**:配了 `GOOGLE_APPLICATION_CREDENTIALS`(指向 Vision 服务账号 JSON,**独立于 `GEMINI_API_KEY`**;**是密钥,放仓库外、别提交**)→ 用 GCV OCR 取**精确框**,几乎不用手调。
- **降级·够用(无 GCV)**:没配 → 你(agent)**直接看 `poster_1.png` 估文字位置**,粗一点没关系,后面在 HTML 编辑器里拖准。

1. **定位文字**:
   - 配了 GCV → `python skill-poster/scripts/poster_text.py ocr --image poster_1.png`(→ `poster_ocr.json`:精确归一化框);
   - 没配 GCV → **跳过 ocr**,你看 `poster_1.png` 自己估每块文字的位置(下一步直接写进 layers)。
2. **消字**得到干净底图(需计费档 image key):
   ```bash
   python skill-poster/scripts/poster_text.py erase --image poster_1.png   # → poster_1_clean.png
   ```
3. **写出文字图层 `poster_text_layers.json`**(内容一律以 `event.json` 为准、纠模型错字;颜色看 `poster_1.png` 取):
   - **有 `poster_ocr.json`(GCV)** → 用精确框换算:`align=center` 时 `x`=框中心、`y`=框顶、`font_scale`=框高/图高;
   - **没有(降级)** → 你看 `poster_1.png` **估** `x`/`y`/`font_scale`(粗估即可,编辑器里再拖准)。
   ```json
   { "layers": [
     {"text": "AI 开发者大会 2026", "x": 0.5, "y": 0.06, "font_scale": 0.05, "color": "#FFFFFF", "bold": true, "align": "center"}
   ] }
   ```
4. **渲染**(纯本地,不需 key):
   ```bash
   python skill-poster/scripts/poster_text.py render --image poster_1_clean.png   # 读 poster_text_layers.json → poster_1_final.png
   ```
5. **改字两种方式**(都不用重新 OCR/消字,改完只重跑 **render**):
   - **对话式**:用户说"标题改成 X / 日期上移 / 换个色",你直接改 `poster_text_layers.json` 再 render;
   - **可视化(可选)**:生成一个浏览器里能**改字/拖位**的预览页让用户自己调:
     ```bash
     python skill-poster/scripts/poster_text.py preview --image poster_1_clean.png
     # → poster_1_edit.html(自包含单文件,底图已内嵌,双击用浏览器打开)
     ```
     用户在页面里改字/拖位 → 点「导出图层 JSON」复制 → 发回给你 → 你写进 `poster_text_layers.json` → 重跑 render 出**高清成品 PNG**。

> 说明:本包**没有持续运行的前端**。`poster_1_final.png` 是**扁平成品图**;`preview` 那个 HTML 是个
> **一次性的本地编辑器**(底图 base64 内嵌、不依赖相对路径,所以不会"图找不到/显示空白"),用完导出图层即可。
> "可编辑"的本质是:**改图层 JSON → 重渲**,而不是一个常驻的可编辑画布。

要点:
- **内容一律以 event.json 为准**——别照抄模型可能拼错的字;位置:有 GCV 走精确框,无 GCV 走估算;
- **降级(无 GCV)位置是估的 → 一定生成 HTML 编辑器(`preview`)让用户拖准,并告诉他"位置是估的、拖一下"**,别把粗定位当成品直接交付;
- 中文字体自动探测系统字体,探不到会提示"装一个 / 放进 assets/fonts/ / 设 `LOEVENT_POSTER_FONT`";
- 渲染会**自动缩字防溢出**;字体观感可能和原图烤的字有差(这是用"可控正确"换"字体完全一致"的预期取舍);
- **成品约 1K 清晰度**:消字用的 `gemini-2.5-flash-image` 原生 ~1024px、不支持 2K/4K,所以可编辑流程的最终图被这步限到 ~1K(社媒/预览够用;要更高清得改用 `gemini-3-pro-image` 消字,但它去字效果较差,是另一个取舍)。

## 易错点(Pitfalls)
- 缺 `event.json`/`host.json` → 先 loevent-init。
- 出不了图≠坏了,大多是 Key 没图像档 → 先 `python engine/doctor.py`,再按降级话术跟用户讲。
- 参考图(`--reference 本地图片`)是可选高级用法,需要装 `Pillow`;不传则用风格知识库。
