# LoEvent AI Skills

一套面向**活动策划**的 AI Agent Skill 工具包。每个 skill 解决活动筹办里的一个具体环节——从把一段活动描述整理成结构化档案，到受众画像、预算、时间线、嘉宾简介、海报、社媒与发布文案。

在你自己的电脑上运行，使用你自己的 API Key，数据留在本地。

## 包含的 Skills

| Skill | 作用 |
|---|---|
| `skill-init` | 入口：把活动描述抽成结构化档案，供其它 skill 消费 |
| `skill-audience` | 目标受众画像 |
| `skill-trends` | 行业趋势 / 话题热点 / 受众痛点调研 |
| `skill-company` | 主办方背景调研与活动策略方向 |
| `skill-guests` | 嘉宾简介（联网调研 + 事实核查） |
| `skill-host-bio` | 主办方公司简介 |
| `skill-budget` | 分项预算估算 |
| `skill-timeline` | 筹备时间线 |
| `skill-social` | 社交媒体文案（小红书 / X / 社群） |
| `skill-luma` | Luma 风格活动发布文案 |
| `skill-poster` | 活动宣传海报 |
| `skill-eventplanner` | 完整活动策划方案 |

所有 skill 共享一个内核 `engine/`，并通过工作目录里的本地文件互相传递上下文。

## 快速开始

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # 填入你的 API Key
python engine/doctor.py         # 环境自检

# 从活动描述起步，生成结构化档案
python skill-init/scripts/init_event.py --text "9月20日在上海办一场面向AI开发者的发布会…"
```

详见各 skill 目录下的 `SKILL.md`，以及 [`references/SETUP.md`](references/SETUP.md)。

## License

[MIT](./LICENSE) © 2026 Gencosmo
