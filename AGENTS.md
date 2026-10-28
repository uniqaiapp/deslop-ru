# AGENTS.md

This repository is an agent skill. The full instructions are in `SKILL.md`; read it first.

## Working in this repo

- Zero dependencies: Python 3.9+ standard library only. Do not add packages, lock files or a `requirements.txt`.
- Run tests: `python3 tests/run.py`. They finish in a few seconds and need no network.
- After changing a pattern in `scripts/deslop.py`, run `python3 scripts/regen_examples.py` and commit the regenerated `examples/reports/` and `references/patterns.md`; the tests compare them byte for byte.
- Keep `SKILL.md` under 500 lines; long material goes to `references/`.
- Every number in `README.md` and `README.ru.md` (pattern counts, scores) must come from `python3 scripts/deslop.py stats` or from `examples/reports/`; the tests check the counts.
- Author and maintainer is UniqAI <support@uniqai.app>; do not add personal names anywhere, including commit messages.

## Using this skill from another project

Clone or copy this repo, then follow "Install" in `README.md`. The short version: when the user asks to remove AI slop or ИИ-штампы from a Russian or English text, follow `SKILL.md`; run `python3 scripts/deslop.py check <file>` before and after the rewrite.
