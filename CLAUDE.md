# CLAUDE.md

本项目的 agent 公约(setup、如何挑/调用 skill、退出码、Key、do-not-touch)统一见:

@AGENTS.md

**Claude Code 专有**:你会自动读 `skill-*/SKILL.md` 的 frontmatter 并按 `description` 触发对应 skill,
缺 key 时用 `AskUserQuestion` 收集(见 `references/API-KEY.md`)。其余一律照 AGENTS.md。
