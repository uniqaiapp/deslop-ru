<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.svg">
  <img alt="deslop-ru: Remove AI slop from Russian text" src="assets/banner.svg" width="1280" height="320">
</picture>

<h1>deslop-ru: remove AI slop from Russian text</h1>

[![License: MIT](https://img.shields.io/badge/license-MIT-d1fe17?style=flat-square&labelColor=0d0f12)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-d1fe17?style=flat-square&labelColor=0d0f12)](#install)
[![Cursor](https://img.shields.io/badge/Cursor-rules-d1fe17?style=flat-square&labelColor=0d0f12)](#install)
[![Codex](https://img.shields.io/badge/Codex-AGENTS.md-d1fe17?style=flat-square&labelColor=0d0f12)](#install)
[![UniqAI](https://img.shields.io/badge/made_by-UniqAI-fdfc07?style=flat-square&labelColor=0d0f12)](https://uniqai.app/?utm_source=github&utm_medium=readme&utm_campaign=deslop-ru)

**Finds and rewrites the phrases that make Russian text sound generated.**

[Quickstart](#quickstart) · [How it works](#how-it-works) · [Pattern categories](#pattern-categories) · [Examples](#examples) · [Install](#install) · [FAQ](#faq)

[Русская версия](README.ru.md)

</div>

deslop-ru removes AI slop from Russian text as a skill for Claude Code, Cursor and Codex, plus a dependency-free Python checker that flags 119 patterns (85 Russian, 34 English) in 10 categories and 7 structure checks, with line numbers and a score. It is for editors, SMM managers, Telegram channel authors, students and developers who write Russian docs and want a draft checked, or rewritten in their own voice, before it goes out.

| **Checker with line numbers** | **Rewrite that keeps your voice** | **Safe cuts, no model needed** |
|:---|:---|:---|
| `scripts/deslop.py` prints every hit with category, phrase and a fix hint, then a 0–100 score. Exit code for CI. | The skill rewrites by category (канцелярит, calques, hype, empty intros and outros) and lists what it changed. Facts, numbers and register stay. | `strip` mode deletes only the 36 phrases whose removal never changes meaning and fixes capitalisation. |

## Quickstart

```bash
git clone https://github.com/uniqaiapp/deslop-ru
python3 deslop-ru/scripts/deslop.py check deslop-ru/examples/telegram-post.before.md
```

You see each flagged line with its category and a one-line fix, then the score. Pipe your own text with `python3 scripts/deslop.py check -`.

## Demo

<img alt="deslop-ru demo: the checker on a Telegram post before and after the rewrite, 100/100 down to 0/100" src="assets/demo.svg" width="820">

## How it works

1. **Measure.** `check` runs 119 regex patterns (ё folded to е, stems for Russian morphology) over the text and 7 structure checks over its form: emoji as bullets, dash density, bold labels in every bullet, list walls, exclamation marks, emoji in headings, paragraphs of identical length. Each hit has a weight from 1 to 3.
2. **Score.** `score = 8 × weighted hits per 100 words`, capped at 100. Bands: under 10 clean, 10–29 light, 30–59 heavy, 60 and above reads like a bot. The bands are a convention of this repo, not an external measurement; density checks are skipped under 40 words.
3. **Cut.** `strip` removes the 36 patterns marked as safe cuts (`Важно отметить, что X` → `X`) and recapitalises. It never touches a fact.
4. **Rewrite.** The skill in [`SKILL.md`](SKILL.md) takes it from there, category by category: verbal nouns back to verbs, hype adjectives replaced by the fact behind them or deleted, triplets reduced to one, intros and outros that say nothing removed. It returns the clean text plus a short list of what changed.
5. **Audit mode** reports without rewriting: category table, form metrics, the five fixes to do first.

Every number above comes from `python3 scripts/deslop.py stats`; the tests fail if this README drifts from the script.

```
scripts/deslop.py check  file.md     hits + score          exit 1 with --fail-over N
scripts/deslop.py audit  file.md     breakdown + verdict   --json for machines
scripts/deslop.py strip  file.md     safe cuts only        --in-place to write back
scripts/deslop.py stats              pattern counts
```

## Pattern categories

| Category | What it catches | Example |
|---|---|---|
| `intro` | Openers that say nothing | в современном мире, давайте разберёмся, не секрет, что |
| `filler` | Connectives that promise instead of show | важно отметить, безусловно, таким образом |
| `bureau` | Канцелярит | данный, осуществлять, в рамках, является, функционал |
| `calque` | English marketing calques | погрузимся, на новый уровень, это не просто X, а Y, бесшовный |
| `hype` | Evaluation instead of fact | уникальный, идеально подходит, широкий спектр, максимально удобно |
| `triplet` | Three adjectives or nouns in a row | быстрый, удобный и надёжный |
| `outro` | Conclusions that repeat the text | подводя итог, надеюсь, было полезно, выбор за вами |
| `chat` | Assistant residue | Конечно!, вот несколько советов:, надеюсь, это поможет |
| `rhetoric` | Tics placed every other paragraph | знаете ли вы, спойлер:, и вот почему, звучит знакомо? |
| `structure` | Form, not phrases | emoji bullets, list walls, a dash in every sentence, bold label per bullet |

The full table with ids, fix hints and weights is in [`references/patterns.md`](references/patterns.md), generated from the script. The English set covers the same categories with 34 patterns (`delve`, `testament to`, `it's not just X, it's Y`, `navigate the landscape`).

## Examples

Six before/after pairs in [`examples/`](examples/README.md). The "after" texts are hand-written rewrites; the reports in `examples/reports/` are the checker's actual output and are reproduced byte for byte by the tests.

| Example | Before | After |
|---|---|---|
| Telegram post, coffee roaster: `examples/telegram-post.before.md` | 100/100 | 0/100 |
| Product card, backpack: `examples/product-card.before.md` | 100/100 | 0/100 |
| Blog intro, procrastination: `examples/blog-intro.before.md` | 100/100 | 0/100 |
| Chat answer pasted as an article: `examples/chat-answer.before.md` | 100/100 | 0/100 |
| Release notes, mostly fine: `examples/release-notes.before.md` | 39/100 | 0/100 |
| English newsletter: `examples/newsletter.before.md` | 100/100 | 0/100 |

<details>
<summary><b>Telegram post: before → after</b></summary>

**Before** (score 100, 18 hits; full report in `examples/reports/telegram-post.check.txt`)

```text
🚀 В современном мире, где всё меняется с невероятной скоростью, важно отметить,
что качественный кофе — это не просто напиток, а настоящий ритуал!

Давайте разберёмся, почему наша новая обжарка — это именно то, что вам нужно.

✅ Уникальный вкус — тщательно отобранные зёрна из Эфиопии
✅ Инновационный подход — обжарка по авторскому профилю
…
Подводя итог, можно с уверенностью сказать: это тот самый вкус, который вы искали.
```

**After** (score 0)

```text
Новая обжарка: Эфиопия, Иргачефф, лот 14.

Зерно с кооператива в Гедео, высота 1 900 м, мытая обработка. Обжарили светло,
под фильтр: в чашке абрикос, чай и немного бергамота. В эспрессо тоже работает,
но будет кислее, чем привычная бразилия.

Пачка 250 г, зип-лок с клапаном. Лучше всего с 5-го по 30-й день после обжарки.
```

What changed: the opener became the most specific fact (origin, lot); every adjective became the thing it stood for (taste notes, altitude, process); the conclusion and the engagement bait went; one concrete offer stayed.

</details>

<details>
<summary><b>Release notes: a light case and what <code>strip</code> does on its own</b></summary>

```text
$ python3 scripts/deslop.py check --no-fix examples/release-notes.before.md
examples/release-notes.before.md: 123 слов, язык ru
  стр. 3   [filler] Важно отметить, что  <- важно отметить
  стр. 5   [calque] бесшовную  <- бесшовный (seamless)
  стр. 7   [bureau] функционал
  оценка: 39/100 (заметно); filler 1, calque 1, bureau 1
```

`strip` removes the first hit by itself (`Важно отметить, что в этой версии` → `В этой версии`); the other two need a human or the skill, because the fix is a different word, not a deletion.

</details>

<details>
<summary><b>Audit mode</b></summary>

```text
$ python3 scripts/deslop.py audit examples/blog-intro.before.md
АУДИТ examples/blog-intro.before.md
слов: 214   язык: ru   оценка: 100/100 (читается как бот)
По категориям
  intro      Пустые зачины              4  ####
  outro      Пустые выводы              5  #####
  structure  Структура                  4  ####
  …
Что сделать в первую очередь
  1. в эпоху цифровых технологий (стр. 3): Уберите. Читатель знает, какой сейчас век.
  2. не секрет, что (стр. 3): Уберите. Если не секрет, зачем говорить.
```

Full output: `examples/reports/blog-intro.audit.txt`.

</details>

## Install

Works with every agent that reads instruction files. Pick yours. Requirements: Python 3.9+. No packages to install.

<details open>
<summary><b>Claude Code</b></summary>

```bash
# user-level
git clone https://github.com/uniqaiapp/deslop-ru ~/.claude/skills/deslop-ru
# or project-level
git clone https://github.com/uniqaiapp/deslop-ru .claude/skills/deslop-ru
# or via the skills CLI
npx skills add uniqaiapp/deslop-ru
```

Then `/deslop-ru` in any session, or just paste a draft and ask to «убрать ИИ-штампы»; the skill's `description` triggers it. As a plugin, once the uniqaiapp marketplace is published: `/plugin marketplace add uniqaiapp/skills` then `/plugin install deslop-ru@uniqaiapp`.

</details>

<details>
<summary><b>Cursor</b></summary>

Copy [`.cursor/rules/deslop-ru.mdc`](.cursor/rules/deslop-ru.mdc) into your project's `.cursor/rules/`, together with `SKILL.md`, `scripts/` and `references/`. The rule embeds the skill with `@SKILL.md`.

</details>

<details>
<summary><b>Codex / any AGENTS.md agent</b></summary>

Copy `SKILL.md`, `scripts/` and `references/` into `.agents/skills/deslop-ru/` and add the snippet from [`codex/INSTRUCTIONS.md`](codex/INSTRUCTIONS.md) to your `AGENTS.md`. This repo's own [`AGENTS.md`](AGENTS.md) shows the shape.

</details>

<details>
<summary><b>Plain prompt or CI</b></summary>

Paste [`SKILL.md`](SKILL.md) into the system prompt of any model; it has no agent-specific syntax outside the frontmatter. For CI, gate on the score:

```bash
python3 scripts/deslop.py check --fail-over 20 docs/*.md
```

</details>

## FAQ

<details>
<summary><b>Does a score of 0 mean a human wrote it?</b></summary>

No. It means none of the 119 phrases and 7 form checks fired. A bland text that avoids the list passes; a vivid text by a person who likes «безусловно» gets flagged. The score is a reading aid, not a detector, and the repo does not try to beat detectors either.

</details>

<details>
<summary><b>Why not just ask the model to "write like a human"?</b></summary>

Because the model does not know which of its habits you mean. The pattern list is the specification: the checker tells the model (and you) exactly which line, which phrase, which category, and the skill has one rule per category for what to put there instead.

</details>

<details>
<summary><b>Will it flag legitimate words like «данные» or «эффективность»?</b></summary>

«Данные» (data) is excluded from the «данный» rule. «Эффективный», «актуальный», «экосистема» carry weight 1 and do get flagged in technical text where they are fine; the skill is told to leave them and say so. Open an issue with the sentence if a rule misfires often; the regex is one line.

</details>

<details>
<summary><b>English?</b></summary>

Yes, with a smaller set (34 patterns) and the same structure checks; language is detected automatically or forced with `--lang en`. For English-first work there are dedicated tools; this one earns its place on Russian text, where English lists catch nothing.

</details>

<details>
<summary><b>Where do the numbers in this README come from?</b></summary>

`python3 scripts/deslop.py stats` for the pattern counts and `examples/reports/scores.txt` for the example scores. `python3 tests/run.py` fails if either drifts.

</details>

## Related

- [token-diet](https://github.com/uniqaiapp/token-diet): cut prompt and context tokens without losing meaning: measurable rules, a stdlib estimator, and before/after examples.
- [skill-shrinker](https://github.com/uniqaiapp/skill-shrinker): shrink any SKILL.md or agent instruction file: measures size, moves long material to references, keeps the triggers intact.
- [model-router](https://github.com/uniqaiapp/model-router): pick the cheapest model that can do the job: a rule table and a stdlib script that routes tasks by type, length and risk.

## Contributing

Issues and pull requests are welcome. Keep changes small and include a before/after sentence in the PR description.
See [CONTRIBUTING.md](CONTRIBUTING.md) for the local checks (`python3 tests/run.py`, no dependencies) and how to add a pattern.

## License

[MIT](LICENSE) © UniqAI

---

<div align="center">

<sub>Made by <a href="https://uniqai.app/?utm_source=github&utm_medium=readme&utm_campaign=deslop-ru">UniqAI</a>, an AI photo, video and chat app. The Russian pages on uniqai.app are written with the same rules.</sub>

</div>
