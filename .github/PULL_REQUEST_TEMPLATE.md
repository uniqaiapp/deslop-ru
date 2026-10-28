## What changed

## Before / after

One sentence the change affects, as it is flagged (or rewritten) before and after this PR:

```text
before:
after:
```

## How to test

```bash
python3 tests/run.py
python3 scripts/regen_examples.py && git diff --stat   # should be empty unless you changed a pattern or example
```

## Honesty check

- [ ] No new numbers in README/SKILL, or every new number comes from `scripts/deslop.py stats` or `examples/reports/`
- [ ] No personal names, real user content or secrets added
