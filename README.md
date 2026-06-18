# loevent-ai · Agent Skill bundle

把 LoEvent 的 AI 能力做成**别人能装来用的工具包**:用户用自己的 Gemini API Key、在自己电脑上跑,不连我们的后端、不碰数据库。

这是方案 [`services/ai_tools/docs/LoEvent-AI能力拆分为Skill-完整方案.md`](../docs/LoEvent-AI能力拆分为Skill-完整方案.md) 的落地实现。
**所有代码都在本文件夹内,原后端代码一行未动**(prompt/schema 是从后端逐字复制进 `engine/`)。

## 目录

```
skill_bundle/
├── engine/                 # 共享内核(只一份,所有 skill 依赖它)
│   ├── llm_client.py       #   单 Key Gemini 客户端(塌缩 NanoKeyPool、去 project 路由、去 DB 日志)
│   ├── config_loader.py    #   prompt YAML 加载 + Jinja2 沙箱渲染
│   ├── model_config.py     #   模型常量 + 映射(与后端 ai_config 顶部一致)
│   ├── context_local.py    #   读写本地 JSON(替代 MongoDB)
│   ├── doctor.py           #   环境自检
│   ├── config/             #   逐字复制的 prompt YAML
│   └── schemas/            #   逐字复制的输出 schema
├── skill-init/             # 入口:活动描述 → event/host/plan.json
├── skill-audience/         # 目标受众画像
├── skill-trends/           # 行业趋势/话题/痛点(grounding)
├── skill-company/          # 公司背景调研 + vibe(grounding,内部并行)
├── skill-guests/           # 嘉宾简介调研(grounding)
├── skill-social/           # 社媒文案(小红书/X/社区,540 md 知识树)
├── skill-poster/           # 海报生成(图像档 + 降级)
├── skill-budget/           # 预算(grounding 查汇率/场地)
├── skill-timeline/         # 筹备时间线
├── skill-host-bio/         # 主办方简介(url_context 读官网)
├── skill-luma/             # Luma 活动描述长短文案
├── skill-eventplanner/     # 活动策划全案(干净版:多节点串联,流水线型)
├── templates/              # 9 份输入示例(各 skill 的 *_input.json;event/host 由 skill-init 生成,不在此)
├── references/SETUP.md     # 给 agent 跑的环境 runbook
├── requirements.txt / .env.example
└── README.md
```

> **engine 共享内核 + 12 个 skill**:11 个售货机型叶子(init / audience / trends / company / guests / social / poster / budget / timeline / host-bio / luma)+ 1 个流水线型 `skill-eventplanner`(活动策划全案,干净版重构)。
> 全部跑通「init 产上下文 → 各叶子消费 plan.json → Claude 按 SKILL.md 整理输出」的单机链路;每个 SKILL.md 都含「结果呈现」段(结构化结果由 Claude 整理后呈现,不甩原始 JSON)。

## 快速开始

```bash
cd skill_bundle
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # 填入 GEMINI_API_KEY
python engine/doctor.py         # 自检

# 从活动描述起步:skill-init 先把上下文落成 event.json/host.json/plan.json
python skill-init/scripts/init_event.py --text "9月20日在上海办一场面向AI开发者的发布会…"

# 再跑任意叶子 skill 消费上面的上下文(不连后端、不连 DB):
python skill-audience/scripts/run.py
```

> `templates/` 里的 `*_input.json` 只是各 skill 的**输入示例**(比如 audience 的 GTM 矩阵);
> 真实上下文(event/host/plan)由 `skill-init` 生成,不靠复制样本。

## 设计要点

- **每个 skill = 给 agent 看的 `SKILL.md`(说明书)+ `scripts/`(干活的脚本)**。脚本吐结构化 JSON;
  **结果由 Claude 按 SKILL.md 的「结果呈现」段整理成可读格式再给用户**,不直接甩 JSON。
- skill 之间靠工作目录里的本地 JSON(`plan.json` 累加器)互相传递,不需要数据库。
- grounding(Google Search)与后端一致,走默认文本模型 `gemini-3-flash-preview`。

## License

[MIT](./LICENSE) © 2026 LoEvent
