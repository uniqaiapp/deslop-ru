---
name: False positive or missed pattern
about: The checker flagged a fine sentence, or missed an obvious one
title: "[pattern] "
labels: pattern
---

**The sentence** (paste it as is, in Russian or English)

```text

```

**What happened**

- [ ] flagged but it is fine (false positive): rule id from the output, e.g. `ru.hype.effective`
- [ ] not flagged but it should be (missed): which category you think it belongs to

**Command and output**

```text
python3 scripts/deslop.py check --no-fix file.md
```

**Python version** (`python3 --version`):
