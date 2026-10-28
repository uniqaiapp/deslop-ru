# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-10-28

### Added

- `SKILL.md`: the rewriting skill with per-category rules, voice rules, audit mode and English mode.
- `scripts/deslop.py`: zero-dependency checker with `check`, `audit`, `strip`, `stats` and `patterns` modes; 119 patterns (85 Russian, 34 English) in 10 categories plus 7 structure checks; score and exit code for CI.
- `references/patterns.md` (generated) and `references/rewrite-guide.md`.
- Six before/after examples with committed checker reports, reproduced byte for byte by the tests.
- Adapters for Claude Code (`.claude-plugin/plugin.json`), Cursor (`.cursor/rules/deslop-ru.mdc`), Codex (`codex/INSTRUCTIONS.md`) and generic `AGENTS.md`.
- English and Russian READMEs, CI workflow, issue and PR templates.
