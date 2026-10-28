---
name: deslop-ru
description: Removes AI-writing patterns (ИИ-штампы) from Russian text and, in a secondary mode, English: empty openers like «в современном мире» and «давайте разберёмся», connectives like «важно отметить», канцелярит («данный», «осуществлять», «в рамках»), English calques («погрузимся», «на новый уровень», «это не просто X, это Y»), hype adjectives, triplets, empty conclusions, chat residue («Конечно!», «Надеюсь, это поможет») and emoji/dash/list-wall structure. Rewrites the draft in the author's voice and lists every change, or in audit mode only reports. Ships scripts/deslop.py, a zero-dependency checker with line numbers and a score. Use when the user asks to remove AI slop, убрать ИИ-штампы, очеловечить текст, сделать текст живым, says a text «звучит как нейросеть» or «написано ChatGPT», wants a пост/статью/описание товара/рассылку checked before publishing, or pastes a Russian draft and asks to clean it. Not for translation, fact-checking, SEO keyword stuffing, or bypassing AI detectors.
license: MIT
metadata:
  version: 0.1.0
  author: UniqAI
  homepage: https://github.com/uniqaiapp/deslop-ru
---

# deslop-ru: remove AI slop from Russian text

You take a Russian (or English) draft that sounds generated and return the same text written by a person: same facts, same voice, no filler. The usual trigger is a user pasting a post, article, product card or newsletter and asking to «убрать ИИ-штампы», «очеловечить», «сделать по-человечески», or saying it «звучит как ChatGPT».

## When to use

- The user pastes Russian text and asks to clean it, humanize it, make it sound less like a bot, or «переписать живым языком».
- The user is a content creator, SMM manager, Telegram channel author, editor or developer writing Russian docs, and wants a draft checked before publishing.
- The user asks for an audit only: «что здесь выдаёт нейросеть?», «оцени текст», «найди штампы» (see Audit mode).
- The text is English and the user asks for the same cleanup (English mode; smaller pattern set).
- A CI or pre-publish step needs a numeric gate: `python3 scripts/deslop.py check --fail-over 20 file.md`.

## When NOT to use

- Translation, summarising or expanding text. This skill keeps length roughly the same or shorter.
- Fact-checking. It does not verify claims; it removes claims that are not claims («уникальный», «высокое качество»).
- Legal, medical or official documents where канцелярит is the required register. Offer the audit, do not rewrite.
- Bypassing AI-content detectors. The goal is readable text, not an evasion. Say so if asked.
- Texts under about 40 words: the score is unreliable there, use judgement instead of the number.

## How it works

1. **Measure first.** Run `python3 scripts/deslop.py check <file>` (or pipe the text to `python3 scripts/deslop.py check -`). It prints every hit with line number, category, the matched phrase and a fix hint, then a score 0–100. If the text is not in a file, save it to a temp file; the script has no dependencies. Run `audit` instead of `check` when the user wants an overview rather than a list.
2. **Decide the mode.** Audit mode: report, do not rewrite (section "Audit mode"). Rewrite mode: continue.
3. **Safe cuts.** `python3 scripts/deslop.py strip <file>` deletes only phrases whose removal never changes meaning (36 of the patterns, marked `cut` in `references/patterns.md`) and fixes capitalisation. Use its output as the starting point; it never touches facts.
4. **Rewrite by category** using the rules below. Work paragraph by paragraph. Keep the author's sentence rhythm where it is not the problem.
5. **Check yourself.** Run `check` on the result. Target: score under 10 and no `intro`, `outro` or `chat` hits. If a hit is a false positive (see Limits), leave the text and say so.
6. **Return** the rewritten text, then a short list «Что изменил» (or "What changed") with one line per change type, not per edit. Never return a diff only; the user needs the clean text to copy.

## Rewrite rules by category

The checker's categories map to the rules below. `references/patterns.md` has the full list with regexes; `references/rewrite-guide.md` has longer before/after pairs.

**intro, пустые зачины.** Delete the first sentence if it is «в современном мире», «в наше время», «не секрет, что», «давайте разберёмся», «в этой статье мы». Start with the most specific fact in the text: a number, a date, a name, a change. If the text has no such fact, ask the user for one in a single question, or start with the strongest claim.

**filler, пустые вводные.** «Важно отметить, что X» becomes «X». «Безусловно, X» becomes «X». «Таким образом,» between two sentences is deleted; if the second sentence really follows from the first, the reader sees it. Keep «но», «а», «поэтому», «зато»: they carry logic.

**bureau, канцелярит.** Verbal nouns become verbs: «осуществляет защиту» → «защищает», «производит оценку» → «оценивает», «обеспечивает размещение» → «вмещает». «Данный» → «этот» or nothing. «Является» → dash or nothing: «рюкзак является оптимальным выбором» → «рюкзак подходит для…» with a concrete use. «В рамках», «с целью», «в связи с этим», «в случае если» → «в», «чтобы», «поэтому», «если». «Функционал» → «функции». Exception: the user explicitly writes for a government or legal audience; then only trim, do not change register.

**calque, кальки.** «Погрузимся» → delete. «На новый уровень», «раскрыть потенциал», «меняет правила игры» → replace with what actually changes, measured if possible («экспорт за 4 секунды вместо 40»). «Это не просто X, а Y» → «Y» alone. «В мире маркетинга» → «в маркетинге». «Бесшовный» → say what the user does not have to do («без переключения вкладок»). «Будь то X или Y» → name the real audience or drop.

**hype, оценочные штампы.** Every evaluative adjective is replaced by the fact that justifies it or deleted. «Уникальный вкус» → what the taste is (апельсин, чай, бергамот). «Высокое качество» → material, tolerance, warranty. «Широкий спектр карманов» → how many and for what. «Идеально подходит для» → «подходит для» plus one condition where it does not. If there is no fact behind the adjective, ask the user once or delete the adjective; never invent a fact.

**triplet, тройки.** «Быстрый, удобный и надёжный» → keep the one that the next sentence proves. Three abstract nouns («эффективность, надёжность и масштабируемость») → one, shown on an example.

**outro, пустые выводы.** Delete «подводя итог», «в заключение», «надеюсь, было полезно», «выбор за вами». If the last paragraph only repeats the text, delete the paragraph. If it adds one new thing (next step, a caveat, a date), keep that one sentence as the ending. One call to action per post, concrete («напишите в комментариях, какой помол» rather than «делитесь мнением»).

**chat, следы чата.** Delete «Конечно!», «Отличный вопрос», «Вот несколько советов:», «Надеюсь, это поможет», «Если остались вопросы, обращайтесь». Turn «рекомендуется сделать X» into the imperative «сделайте X». Delete any sentence where the text refers to itself as an AI.

**rhetoric, риторика.** Rhetorical questions («Знаете ли вы, что…?», «Звучит знакомо?») become statements. «Спойлер:», «И вот почему», «Но есть нюанс» are deleted; the next sentence already does the job. «Это не про X. Это про Y.» → «Y».

**structure, форма.** Emoji: at most one per post, never as a bullet, never in a heading. Bold labels in every bullet («**Надёжность:** …») are removed; if the bullets cannot stand without labels, they are not bullets, make them a paragraph. Lists longer than five items are folded into prose or cut. Dashes: if there is a dash in every sentence, replace half with a period or a comma. Exclamation marks: one per text, usually zero. Paragraphs of identical length are a tell; let one be short.

## Voice rules (what you keep)

- Facts, numbers, names, prices, dates, product terms, links, hashtags, and the order of arguments. If a fact looks wrong, flag it in «Что изменил», do not fix it silently.
- The author's register: «ты» stays «ты», «вы» stays «вы», slang stays slang, a joke stays a joke. Humanising is not formalising.
- Quotes and anything in «кавычки» or code blocks, verbatim.
- Length: the result is shorter or equal. Never pad to compensate for cuts.
- Markdown structure the user needs (headings for a long article, a numbered list for steps). Remove decoration, not structure.
- One thing you add: a concrete first sentence, if the original had none and the text contains a fact that can serve. Mark it in «Что изменил».

## Audit mode

Trigger words: «проверь», «оцени», «найди штампы», «что выдаёт нейросеть», «audit», or the user asks not to change the text. Output, in this order:

1. The `audit` block from `python3 scripts/deslop.py audit <file>` (score, categories, form metrics, «что сделать в первую очередь»).
2. Three to five of the worst lines quoted with a one-line rewrite each, so the user sees the method.
3. One sentence on whether the text is worth rewriting or re-drafting from the facts (score above 60 with no concrete facts usually means re-draft).

Do not rewrite the whole text in audit mode even if it is short.

## English mode

Same procedure; the checker switches to the English pattern set automatically (`--lang en` forces it). The English list is shorter (34 patterns against 85 Russian, 119 in total) and the structure checks are identical. Typical English-only rules: «delve», «tapestry», «testament to», «navigate the landscape» are deleted or replaced with the plain word; «it's not just X, it's Y» becomes «Y»; «whether you're a X or a Y» names the real reader or goes.

## Inputs / outputs

| Input | Output |
|---|---|
| Russian or English draft: plain text or Markdown, as a file or pasted | Rewritten text (same format) + «Что изменил» list |
| `check` on a file | Hit list with line numbers, category, phrase, fix hint; score and verdict; exit 1 with `--fail-over N` when score > N |
| `audit` on a file | Category table, form metrics, top fixes; `--json` for machines |
| `strip` on a file | Text with only safe cuts applied (`--in-place` to write back) |
| `stats` | Pattern counts per language and category; the README numbers come from here |

## Examples

Six before/after pairs with the checker's committed output live in `examples/` (see `examples/README.md`). Reproduce any report with, for instance:

```
python3 scripts/deslop.py check --no-fix examples/telegram-post.before.md
python3 scripts/deslop.py audit examples/blog-intro.before.md
python3 scripts/deslop.py strip examples/chat-answer.before.md
```

## Limits

- The checker is a regex list, not a classifier. It flags phrases, not intent, and it will miss a bland text that avoids every phrase on the list. A score of 0 means «no known patterns», not «written by a human».
- False positives exist. «Данные» (data) is excluded from the «данный» rule, but «актуальный» in «актуальная версия», «эффективный» in a technical comparison, or «экосистема» in biology are legitimate. Leave them and say so.
- The score is 8 × weighted hits per 100 words, capped at 100. Bands: under 10 clean, 10–29 light, 30–59 heavy, 60+ reads like a bot. The bands are a convention of this repo, not a measurement of anything external.
- Russian morphology is handled by stem regexes with ё folded to е; rare forms and typos slip through.
- English coverage is deliberately smaller; for English-first work prefer a dedicated English tool and use this one for the shared structure checks.
- The skill does not detect machine translation, plagiarism or factual errors.

## References

- `references/patterns.md`: every pattern with id, category, fix and weight (generated by `python3 scripts/deslop.py patterns --markdown`).
- `references/rewrite-guide.md`: longer before/after pairs per category and the reasoning behind each cut.
- `examples/README.md`: the six example pairs and the commands that produce their reports.
