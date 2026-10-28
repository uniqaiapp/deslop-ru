# Examples

Each example is a pair: `<name>.before.md` is a draft with the usual AI tells, `<name>.after.md` is a hand-written rewrite with the same facts. `reports/` holds the checker's real output for every `before` file; `python3 scripts/regen_examples.py` regenerates it and `tests/test_examples.py` compares byte for byte, so the scores quoted in the READMEs cannot drift.

| Example | Shows | Before | After |
|---|---|---|---|
| `telegram-post` | SMM post: emoji bullets, hype adjectives, calques, engagement bait | 100/100 | 0/100 |
| `product-card` | E-commerce card: канцелярит, «данный», «осуществляет», bold labels | 100/100 | 0/100 |
| `blog-intro` | Article: «в эпоху цифровых технологий», list wall of ten tips, empty conclusion | 100/100 | 0/100 |
| `chat-answer` | Assistant answer pasted as content: «Конечно!», «Вот несколько», «Надеюсь, это поможет» | 100/100 | 0/100 |
| `release-notes` | A mostly fine text with three tells; the light band and what `strip` fixes alone | 39/100 | 0/100 |
| `newsletter` | English mode: «in today's fast-paced world», «game-changer», triplets, «in conclusion» | 100/100 | 0/100 |

Scores: `reports/scores.txt`.

## Commands

From the repo root:

```bash
python3 scripts/deslop.py check --no-fix examples/<name>.before.md   # -> reports/<name>.check.txt
python3 scripts/deslop.py audit examples/<name>.before.md            # -> reports/<name>.audit.txt
python3 scripts/deslop.py strip examples/<name>.before.md            # -> reports/<name>.strip.md
python3 scripts/deslop.py check examples/<name>.after.md             # score under 10
```

## What the rewrites do

The `after` texts are not minimal edits. They follow `SKILL.md`: the opener is the most specific fact; every evaluative adjective is replaced by the thing it stood for or deleted; conclusions that repeat the text are gone; one call to action, concrete. They are shorter than the originals and they contain one honest limitation each (the coffee is sourer as espresso, the backpack needs a cover in heavy rain, the timer method did not work). That last part is not a rule, it is what tends to happen when the hype goes.
