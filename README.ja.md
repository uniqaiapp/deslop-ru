<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.svg">
  <img alt="deslop-ru: Remove AI slop from Russian text" src="assets/banner.svg" width="1280" height="320">
</picture>

<h1>deslop-ru: ロシア語テキストの「AIっぽさ」を取り除く</h1>

[![License: MIT](https://img.shields.io/badge/license-MIT-d1fe17?style=flat-square&labelColor=0d0f12)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-d1fe17?style=flat-square&labelColor=0d0f12)](#インストール)
[![Cursor](https://img.shields.io/badge/Cursor-rules-d1fe17?style=flat-square&labelColor=0d0f12)](#インストール)
[![Codex](https://img.shields.io/badge/Codex-AGENTS.md-d1fe17?style=flat-square&labelColor=0d0f12)](#インストール)
[![UniqAI](https://img.shields.io/badge/made_by-UniqAI-fdfc07?style=flat-square&labelColor=0d0f12)](https://uniqai.app/?utm_source=github&utm_medium=readme-ja&utm_campaign=deslop-ru)

**ロシア語の文章を「AIが書いたもの」に見せてしまう言い回しを見つけて、書き直します。**

[クイックスタート](#クイックスタート) · [仕組み](#仕組み) · [パターンのカテゴリ](#パターンのカテゴリ) · [使用例](#使用例) · [インストール](#インストール) · [よくある質問](#よくある質問)

</div>

[English](README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português (BR)](README.pt-BR.md) · 日本語 · [한국어](README.ko.md)

deslop-ru は、ロシア語テキストから AI 特有の定型表現（AI slop）を取り除くツールです。Claude Code、Cursor、Codex 向けのスキルに加えて、依存関係ゼロの Python 製チェッカーが付属します。チェッカーは 10 カテゴリ 119 パターン（ロシア語 85、英語 34）と 7 項目の構成チェックで該当箇所を行番号付きで示し、スコアを付けます。対象は、ロシア語でドキュメントを書く編集者、SNS 担当者、Telegram チャンネルの運営者、学生、開発者で、公開前に下書きをチェックしたい、あるいは自分の声のまま書き直したい人です。

| **行番号付きのチェッカー** | **自分の声を保った書き直し** | **モデル不要の安全な削除** |
|:---|:---|:---|
| `scripts/deslop.py` は検出箇所ごとにカテゴリ、該当フレーズ、修正のヒントを出力し、最後に 0〜100 のスコアを表示します。CI 向けに終了コードも返します。 | スキルはカテゴリ単位で書き直し（お役所言葉、英語直訳、誇張表現、中身のない導入と結び）、何を変えたかを列挙します。事実、数値、文体はそのままです。 | `strip` モードは、削除しても意味が変わらない 36 のフレーズだけを消し、大文字小文字を直します。 |

## クイックスタート

```bash
git clone https://github.com/uniqaiapp/deslop-ru
python3 deslop-ru/scripts/deslop.py check deslop-ru/examples/telegram-post.before.md
```

検出された各行がカテゴリと一行の修正案つきで表示され、最後にスコアが出ます。自分のテキストを標準入力から渡すには `python3 scripts/deslop.py check -` を使います。

## デモ

<img alt="deslop-ru demo: the checker on a Telegram post before and after the rewrite, 100/100 down to 0/100" src="assets/demo.svg" width="820">

## 仕組み

1. **測定。** `check` は 119 本の正規表現（ё は е に正規化、ロシア語の語形変化は語幹で対応）をテキストに適用し、さらに体裁に対して 7 項目の構成チェックを行います。箇条書きの記号としての絵文字、ダッシュの密度、全項目に付いた太字ラベル、箇条書きの壁、感嘆符、見出し内の絵文字、同じ長さの段落の連続です。検出ごとに 1〜3 の重みが付きます。
2. **採点。** `スコア = 8 × 100 語あたりの重み付き検出数`、上限は 100 です。目安は、10 未満がクリーン、10〜29 が軽度、30〜59 が重度、60 以上は bot の文章のように読めます。この区分はこのリポジトリ内の取り決めであり、外部の指標ではありません。40 語未満では密度チェックをスキップします。
3. **削除。** `strip` は安全な削除として印の付いた 36 パターンを取り除き（`Важно отметить, что X` → `X`）、先頭の大文字を直します。事実には一切触れません。
4. **書き直し。** そこから先は [`SKILL.md`](SKILL.md) のスキルがカテゴリごとに引き継ぎます。動詞由来の名詞を動詞に戻す、誇張の形容詞をその裏にある事実に置き換えるか削る、三つ並べた語を一つにする、何も言っていない導入と結びを外す。クリーンになったテキストと、変更点の短いリストを返します。
5. **監査モード**は書き直さずに報告だけ行います。カテゴリ別の表、体裁の指標、最初に直すべき 5 点です。

上記の数値はすべて `python3 scripts/deslop.py stats` の出力です。この README がスクリプトとずれるとテストが失敗します。

```
scripts/deslop.py check  file.md     hits + score          exit 1 with --fail-over N
scripts/deslop.py audit  file.md     breakdown + verdict   --json for machines
scripts/deslop.py strip  file.md     safe cuts only        --in-place to write back
scripts/deslop.py stats              pattern counts
```

## パターンのカテゴリ

| カテゴリ | 検出するもの | 例 |
|---|---|---|
| `intro` | 何も言っていない書き出し | в современном мире, давайте разберёмся, не секрет, что |
| `filler` | 示す代わりに約束するだけの接続表現 | важно отметить, безусловно, таким образом |
| `bureau` | お役所言葉（канцелярит） | данный, осуществлять, в рамках, является, функционал |
| `calque` | 英語マーケティング表現の直訳 | погрузимся, на новый уровень, это не просто X, а Y, бесшовный |
| `hype` | 事実の代わりの評価 | уникальный, идеально подходит, широкий спектр, максимально удобно |
| `triplet` | 形容詞や名詞の三連続 | быстрый, удобный и надёжный |
| `outro` | 本文を繰り返すだけの結び | подводя итог, надеюсь, было полезно, выбор за вами |
| `chat` | アシスタントとの会話の名残 | Конечно!, вот несколько советов:, надеюсь, это поможет |
| `rhetoric` | 段落おきに現れる決まり文句 | знаете ли вы, спойлер:, и вот почему, звучит знакомо? |
| `structure` | フレーズではなく体裁 | 絵文字の箇条書き、箇条書きの壁、毎文のダッシュ、項目ごとの太字ラベル |

id、修正のヒント、重みを含む完全な表は [`references/patterns.md`](references/patterns.md) にあり、スクリプトから生成されます。英語セットは同じカテゴリを 34 パターンでカバーします（`delve`、`testament to`、`it's not just X, it's Y`、`navigate the landscape`）。

## 使用例

[`examples/`](examples/README.md) に 6 組の before/after があります。「after」のテキストは人が書き直したものです。`examples/reports/` のレポートはチェッカーの実際の出力で、テストがバイト単位で再現します。

| 例 | Before | After |
|---|---|---|
| Telegram の投稿、コーヒー焙煎所: `examples/telegram-post.before.md` | 100/100 | 0/100 |
| 商品ページ、バックパック: `examples/product-card.before.md` | 100/100 | 0/100 |
| ブログの導入、先延ばし癖について: `examples/blog-intro.before.md` | 100/100 | 0/100 |
| チャットの回答を記事として貼ったもの: `examples/chat-answer.before.md` | 100/100 | 0/100 |
| リリースノート、ほぼ問題なし: `examples/release-notes.before.md` | 39/100 | 0/100 |
| 英語のニュースレター: `examples/newsletter.before.md` | 100/100 | 0/100 |

<details>
<summary><b>Telegram の投稿: before → after</b></summary>

**Before**（スコア 100、検出 18 件。完全なレポートは `examples/reports/telegram-post.check.txt`）

```text
🚀 В современном мире, где всё меняется с невероятной скоростью, важно отметить,
что качественный кофе — это не просто напиток, а настоящий ритуал!

Давайте разберёмся, почему наша новая обжарка — это именно то, что вам нужно.

✅ Уникальный вкус — тщательно отобранные зёрна из Эфиопии
✅ Инновационный подход — обжарка по авторскому профилю
…
Подводя итог, можно с уверенностью сказать: это тот самый вкус, который вы искали.
```

**After**（スコア 0）

```text
Новая обжарка: Эфиопия, Иргачефф, лот 14.

Зерно с кооператива в Гедео, высота 1 900 м, мытая обработка. Обжарили светло,
под фильтр: в чашке абрикос, чай и немного бергамота. В эспрессо тоже работает,
но будет кислее, чем привычная бразилия.

Пачка 250 г, зип-лок с клапаном. Лучше всего с 5-го по 30-й день после обжарки.
```

変更点: 書き出しがもっとも具体的な事実（産地、ロット）になりました。各形容詞は、それが指していたもの（味のノート、標高、精製方法）に置き換わりました。結びとエンゲージメント狙いの煽りは消え、具体的なオファーが一つ残りました。

</details>

<details>
<summary><b>リリースノート: 軽度のケースと、<code>strip</code> 単体でできること</b></summary>

```text
$ python3 scripts/deslop.py check --no-fix examples/release-notes.before.md
examples/release-notes.before.md: 123 слов, язык ru
  стр. 3   [filler] Важно отметить, что  <- важно отметить
  стр. 5   [calque] бесшовную  <- бесшовный (seamless)
  стр. 7   [bureau] функционал
  оценка: 39/100 (заметно); filler 1, calque 1, bureau 1
```

最初の検出は `strip` だけで取り除けます（`Важно отметить, что в этой версии` → `В этой версии`）。残りの 2 件は人かスキルが必要です。修正が削除ではなく別の語への置き換えだからです。

</details>

<details>
<summary><b>監査モード</b></summary>

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

完全な出力: `examples/reports/blog-intro.audit.txt`。

</details>

## インストール

指示ファイルを読むエージェントならどれでも使えます。お使いのものを選んでください。要件: Python 3.9+。インストールするパッケージはありません。

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

あとは任意のセッションで `/deslop-ru` と入力するか、下書きを貼り付けて「убрать ИИ-штампы」（AI の定型表現を取り除いて）と頼むだけです。スキルの `description` がトリガーになります。プラグインとして使う場合は、uniqaiapp マーケットプレイス公開後に `/plugin marketplace add uniqaiapp/skills` に続けて `/plugin install deslop-ru@uniqaiapp` を実行してください。

</details>

<details>
<summary><b>Cursor</b></summary>

[`.cursor/rules/deslop-ru.mdc`](.cursor/rules/deslop-ru.mdc) を、`SKILL.md`、`scripts/`、`references/` と一緒にプロジェクトの `.cursor/rules/` にコピーします。ルールは `@SKILL.md` でスキルを埋め込みます。

</details>

<details>
<summary><b>Codex / AGENTS.md を読む任意のエージェント</b></summary>

`SKILL.md`、`scripts/`、`references/` を `.agents/skills/deslop-ru/` にコピーし、[`codex/INSTRUCTIONS.md`](codex/INSTRUCTIONS.md) のスニペットを自分の `AGENTS.md` に追加します。このリポジトリ自身の [`AGENTS.md`](AGENTS.md) が書き方の見本です。

</details>

<details>
<summary><b>プレーンなプロンプト、または CI</b></summary>

[`SKILL.md`](SKILL.md) を任意のモデルのシステムプロンプトに貼り付けてください。frontmatter 以外にエージェント固有の構文はありません。CI ではスコアで足切りします。

```bash
python3 scripts/deslop.py check --fail-over 20 docs/*.md
```

</details>

## よくある質問

<details>
<summary><b>スコア 0 なら人間が書いたということですか?</b></summary>

いいえ。119 のフレーズと 7 項目の構成チェックのどれにも該当しなかった、という意味です。リストを避けただけの平板な文章は通りますし、「безусловно」が口癖の人が書いた生き生きとした文章には印が付きます。スコアは読むときの補助であって検出器ではありませんし、このリポジトリは検出器をすり抜けることも目指していません。

</details>

<details>
<summary><b>モデルに「人間らしく書いて」と頼めば済むのでは?</b></summary>

モデルは、自分のどの癖を指しているのか分からないからです。パターン一覧が仕様書の役割を果たします。チェッカーはモデル（とあなた）に、どの行の、どのフレーズが、どのカテゴリかを正確に伝え、スキルにはカテゴリごとに「代わりに何を書くか」のルールが一つずつあります。

</details>

<details>
<summary><b>「данные」や「эффективность」のような普通の語も検出されますか?</b></summary>

「Данные」（データ）は「данный」ルールの対象外です。「Эффективный」「актуальный」「экосистема」は重み 1 で、技術文書で問題なく使われている場合でも検出されます。スキルにはそれらを残して、その旨を伝えるよう指示してあります。あるルールの誤検出が多いなら、その文を添えて issue を立ててください。正規表現は 1 行です。

</details>

<details>
<summary><b>英語には対応していますか?</b></summary>

はい。より小さなセット（34 パターン）と同じ構成チェックで対応します。言語は自動判定されますが、`--lang en` で固定もできます。英語が主体の作業には専用ツールがあります。このツールが真価を発揮するのはロシア語テキストで、英語向けのリストでは何も検出できない領域です。

</details>

<details>
<summary><b>この README の数値はどこから来ていますか?</b></summary>

パターン数は `python3 scripts/deslop.py stats`、例のスコアは `examples/reports/scores.txt` からです。どちらかがずれると `python3 tests/run.py` が失敗します。

</details>

## 関連リポジトリ

- [token-diet](https://github.com/uniqaiapp/token-diet): 意味を失わずにプロンプトとコンテキストのトークンを削減します。測定可能なルール、標準ライブラリだけの見積もりツール、before/after の例。
- [skill-shrinker](https://github.com/uniqaiapp/skill-shrinker): SKILL.md やエージェントの指示ファイルを圧縮します。サイズを測り、長い内容を references に移し、トリガーはそのまま残します。
- [model-router](https://github.com/uniqaiapp/model-router): タスクをこなせる中でもっとも安いモデルを選びます。ルール表と、タスクを種類・長さ・リスクで振り分ける標準ライブラリ製スクリプト。

## コントリビュート

Issue と pull request を歓迎します。変更は小さく保ち、PR の説明に before/after の文を一つ添えてください。
ローカルでのチェック（`python3 tests/run.py`、依存関係なし）とパターンの追加方法は [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

## ライセンス

[MIT](LICENSE) © UniqAI

---

<div align="center">

<sub>Made by <a href="https://uniqai.app/?utm_source=github&utm_medium=readme-ja&utm_campaign=deslop-ru">UniqAI</a>。AI による写真、動画、チャットを一つにまとめたアプリです。uniqai.app のロシア語ページも同じルールで書かれています。</sub>

</div>
