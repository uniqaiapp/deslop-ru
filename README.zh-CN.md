<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.svg">
  <img alt="deslop-ru: Remove AI slop from Russian text" src="assets/banner.svg" width="1280" height="320">
</picture>

<h1>deslop-ru：去除俄语文本中的 AI 味</h1>

[![License: MIT](https://img.shields.io/badge/license-MIT-d1fe17?style=flat-square&labelColor=0d0f12)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-d1fe17?style=flat-square&labelColor=0d0f12)](#安装)
[![Cursor](https://img.shields.io/badge/Cursor-rules-d1fe17?style=flat-square&labelColor=0d0f12)](#安装)
[![Codex](https://img.shields.io/badge/Codex-AGENTS.md-d1fe17?style=flat-square&labelColor=0d0f12)](#安装)
[![UniqAI](https://img.shields.io/badge/made_by-UniqAI-fdfc07?style=flat-square&labelColor=0d0f12)](https://uniqai.app/?utm_source=github&utm_medium=readme-zh-cn&utm_campaign=deslop-ru)

**找出并改写那些让俄语文本「一看就是 AI 写的」的句式。**

[快速开始](#快速开始) · [工作原理](#工作原理) · [模式分类](#模式分类) · [示例](#示例) · [安装](#安装) · [常见问题](#常见问题)

</div>

[English](README.md) · [Русский](README.ru.md) · 简体中文 · [Español](README.es.md) · [Português (BR)](README.pt-BR.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

deslop-ru 用来去除俄语文本中的 AI 味：它是 Claude Code、Cursor 和 Codex 的 skill，同时附带一个零依赖的 Python 检查器，能标出 10 个类别下的 119 种模式（85 种俄语、34 种英语）并做 7 项结构检查，输出行号和评分。它面向编辑、SMM 运营、Telegram 频道作者、学生，以及用俄语写文档的开发者：在发布之前把草稿检查一遍，或者按自己的语气重写。

| **带行号的检查器** | **保留你语气的重写** | **安全删减，无需模型** |
|:---|:---|:---|
| `scripts/deslop.py` 逐条打印命中：类别、短语和修改提示，最后给出 0–100 的评分。退出码可用于 CI。 | skill 按类别重写（公文腔、英语直译、吹捧词、空洞的开头和结尾）并列出改了什么。事实、数字和语体保持不变。 | `strip` 模式只删除那 36 条删掉也不改变意思的短语，并修正首字母大写。 |

## 快速开始

```bash
git clone https://github.com/uniqaiapp/deslop-ru
python3 deslop-ru/scripts/deslop.py check deslop-ru/examples/telegram-post.before.md
```

你会看到每一行被标记的内容、所属类别和一句话修改建议，最后是评分。检查自己的文本：`python3 scripts/deslop.py check -`，从 stdin 传入即可。

## 演示

<img alt="deslop-ru demo: the checker on a Telegram post before and after the rewrite, 100/100 down to 0/100" src="assets/demo.svg" width="820">

## 工作原理

1. **测量。** `check` 对文本运行 119 条正则（ё 折叠为 е，按词干处理俄语形态变化），再对版式做 7 项结构检查：emoji 当项目符号、破折号密度、每个要点都带加粗标签、列表墙、感叹号、标题里的 emoji、长度完全一致的段落。每次命中的权重为 1 到 3。
2. **评分。** `评分 = 8 × 每 100 词的加权命中数`，上限 100。区间：10 以下干净，10–29 轻微，30–59 严重，60 及以上读起来像机器人。区间是本仓库的约定，不是外部度量；文本不足 40 词时跳过密度检查。
3. **删减。** `strip` 删除标记为安全删减的 36 条模式（`Важно отметить, что X` → `X`）并重新处理首字母大写。它从不碰事实。
4. **重写。** 接下来由 [`SKILL.md`](SKILL.md) 中的 skill 接手，逐类处理：动名词改回动词，吹捧形容词换成背后的事实或直接删掉，三连排比缩成一个，什么都没说的开头和结尾去掉。它返回干净的文本，外加一份简短的改动清单。
5. **审计模式**只报告不重写：分类表、版式指标、最先要做的五处修改。

上面的每个数字都来自 `python3 scripts/deslop.py stats`；如果这份 README 与脚本不一致，测试会失败。

```
scripts/deslop.py check  file.md     hits + score          exit 1 with --fail-over N
scripts/deslop.py audit  file.md     breakdown + verdict   --json for machines
scripts/deslop.py strip  file.md     safe cuts only        --in-place to write back
scripts/deslop.py stats              pattern counts
```

## 模式分类

| 类别 | 捕获什么 | 示例 |
|---|---|---|
| `intro` | 什么都没说的开场白 | в современном мире, давайте разберёмся, не секрет, что |
| `filler` | 只承诺不展示的连接语 | важно отметить, безусловно, таким образом |
| `bureau` | 公文腔（канцелярит） | данный, осуществлять, в рамках, является, функционал |
| `calque` | 英语营销用语的直译 | погрузимся, на новый уровень, это не просто X, а Y, бесшовный |
| `hype` | 用评价代替事实 | уникальный, идеально подходит, широкий спектр, максимально удобно |
| `triplet` | 连续三个形容词或名词 | быстрый, удобный и надёжный |
| `outro` | 把正文再说一遍的结论 | подводя итог, надеюсь, было полезно, выбор за вами |
| `chat` | 助手对话的残留 | Конечно!, вот несколько советов:, надеюсь, это поможет |
| `rhetoric` | 隔一段就出现的套路 | знаете ли вы, спойлер:, и вот почему, звучит знакомо? |
| `structure` | 版式而非短语 | emoji 项目符号、列表墙、每句一个破折号、每个要点一个加粗标签 |

完整表格（含 id、修改提示和权重）见 [`references/patterns.md`](references/patterns.md)，由脚本生成。英语集合覆盖同样的类别，共 34 种模式（`delve`、`testament to`、`it's not just X, it's Y`、`navigate the landscape`）。

## 示例

[`examples/`](examples/README.md) 中有六组前后对照。「后」的文本是人工重写的；`examples/reports/` 中的报告是检查器的真实输出，测试会逐字节复现。

| 示例 | 之前 | 之后 |
|---|---|---|
| Telegram 帖子，咖啡烘焙商：`examples/telegram-post.before.md` | 100/100 | 0/100 |
| 商品详情，双肩包：`examples/product-card.before.md` | 100/100 | 0/100 |
| 博客开头，拖延症：`examples/blog-intro.before.md` | 100/100 | 0/100 |
| 把聊天回答直接贴成文章：`examples/chat-answer.before.md` | 100/100 | 0/100 |
| Release notes，基本没问题：`examples/release-notes.before.md` | 39/100 | 0/100 |
| 英文 newsletter：`examples/newsletter.before.md` | 100/100 | 0/100 |

<details>
<summary><b>Telegram 帖子：前 → 后</b></summary>

**之前**（评分 100，18 处命中；完整报告见 `examples/reports/telegram-post.check.txt`）

```text
🚀 В современном мире, где всё меняется с невероятной скоростью, важно отметить,
что качественный кофе — это не просто напиток, а настоящий ритуал!

Давайте разберёмся, почему наша новая обжарка — это именно то, что вам нужно.

✅ Уникальный вкус — тщательно отобранные зёрна из Эфиопии
✅ Инновационный подход — обжарка по авторскому профилю
…
Подводя итог, можно с уверенностью сказать: это тот самый вкус, который вы искали.
```

**之后**（评分 0）

```text
Новая обжарка: Эфиопия, Иргачефф, лот 14.

Зерно с кооператива в Гедео, высота 1 900 м, мытая обработка. Обжарили светло,
под фильтр: в чашке абрикос, чай и немного бергамота. В эспрессо тоже работает,
но будет кислее, чем привычная бразилия.

Пачка 250 г, зип-лок с клапаном. Лучше всего с 5-го по 30-й день после обжарки.
```

改了什么：开头换成了最具体的事实（产地、批次）；每个形容词都换成了它所指代的东西（风味描述、海拔、处理法）；结论和互动诱饵删掉了；保留了一个具体的卖点。

</details>

<details>
<summary><b>Release notes：轻度案例，以及 <code>strip</code> 单独能做什么</b></summary>

```text
$ python3 scripts/deslop.py check --no-fix examples/release-notes.before.md
examples/release-notes.before.md: 123 слов, язык ru
  стр. 3   [filler] Важно отметить, что  <- важно отметить
  стр. 5   [calque] бесшовную  <- бесшовный (seamless)
  стр. 7   [bureau] функционал
  оценка: 39/100 (заметно); filler 1, calque 1, bureau 1
```

`strip` 自己就能处理第一处命中（`Важно отметить, что в этой версии` → `В этой версии`）；另外两处需要人或 skill 来改，因为修法是换一个词，而不是删掉。

</details>

<details>
<summary><b>审计模式</b></summary>

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

完整输出：`examples/reports/blog-intro.audit.txt`。

</details>

## 安装

任何会读取指令文件的 agent 都能用，选你的那一个。要求：Python 3.9+，无需安装任何包。

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

然后在任意会话中输入 `/deslop-ru`，或者直接粘贴草稿并要求「убрать ИИ-штампы」（去掉 AI 味）；skill 会根据自身的 `description` 触发。作为插件安装（uniqaiapp marketplace 发布后）：先 `/plugin marketplace add uniqaiapp/skills`，再 `/plugin install deslop-ru@uniqaiapp`。

</details>

<details>
<summary><b>Cursor</b></summary>

把 [`.cursor/rules/deslop-ru.mdc`](.cursor/rules/deslop-ru.mdc) 复制到项目的 `.cursor/rules/`，并一起复制 `SKILL.md`、`scripts/` 和 `references/`。规则文件通过 `@SKILL.md` 嵌入 skill。

</details>

<details>
<summary><b>Codex / 任何读取 AGENTS.md 的 agent</b></summary>

把 `SKILL.md`、`scripts/` 和 `references/` 复制到 `.agents/skills/deslop-ru/`，再把 [`codex/INSTRUCTIONS.md`](codex/INSTRUCTIONS.md) 里的片段加进你的 `AGENTS.md`。本仓库自己的 [`AGENTS.md`](AGENTS.md) 就是一个样板。

</details>

<details>
<summary><b>纯提示词或 CI</b></summary>

把 [`SKILL.md`](SKILL.md) 粘贴进任意模型的系统提示词；除了 frontmatter 之外没有任何 agent 专用语法。在 CI 中按评分设门槛：

```bash
python3 scripts/deslop.py check --fail-over 20 docs/*.md
```

</details>

## 常见问题

<details>
<summary><b>评分为 0 就说明是人写的吗？</b></summary>

不是。它只说明 119 条短语和 7 项结构检查都没有触发。避开了列表的平淡文本能通过；爱用「безусловно」的真人写的生动文本反而会被标记。评分是阅读辅助，不是检测器；本仓库也不试图绕过检测器。

</details>

<details>
<summary><b>为什么不直接让模型「写得像人」？</b></summary>

因为模型不知道你指的是它的哪些习惯。模式列表就是规格说明：检查器会准确告诉模型（和你）是哪一行、哪个短语、哪个类别，而 skill 对每个类别都有一条规则，说明该换成什么。

</details>

<details>
<summary><b>会误报「данные」或「эффективность」这类正常用词吗？</b></summary>

「Данные」（数据）已从「данный」规则中排除。「Эффективный」「актуальный」「экосистема」权重为 1，在技术文本里本来用得没问题时也会被标记；skill 被要求保留它们并说明原因。如果某条规则经常误报，带上那句话开个 issue；正则只有一行。

</details>

<details>
<summary><b>支持英语吗？</b></summary>

支持，但集合更小（34 种模式），结构检查相同；语言自动检测，也可以用 `--lang en` 强制指定。以英语为主的工作有专门的工具；这个工具的价值在俄语文本上，英语列表在那里什么也抓不到。

</details>

<details>
<summary><b>这份 README 里的数字从哪来？</b></summary>

模式数量来自 `python3 scripts/deslop.py stats`，示例评分来自 `examples/reports/scores.txt`。两者任一不一致，`python3 tests/run.py` 就会失败。

</details>

## 相关项目

- [token-diet](https://github.com/uniqaiapp/token-diet)：在不丢失含义的前提下削减 prompt 和上下文的 token：可度量的规则、一个纯标准库的估算器，以及前后对照示例。
- [skill-shrinker](https://github.com/uniqaiapp/skill-shrinker)：压缩任意 SKILL.md 或 agent 指令文件：测量大小，把长内容挪到 references，保持触发条件不变。
- [model-router](https://github.com/uniqaiapp/model-router)：挑一个能完成任务的最便宜的模型：一张规则表加一个纯标准库脚本，按类型、长度和风险给任务分配模型。

## 参与贡献

欢迎提交 issue 和 pull request。改动保持小步，并在 PR 描述里附上一句前后对照。
本地检查（`python3 tests/run.py`，零依赖）和如何添加模式，见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

[MIT](LICENSE) © UniqAI

---

<div align="center">

<sub>Made by <a href="https://uniqai.app/?utm_source=github&utm_medium=readme-zh-cn&utm_campaign=deslop-ru">UniqAI</a>，一款集 AI 照片、视频和聊天于一体的应用。uniqai.app 的俄语页面也是按同一套规则写的。</sub>

</div>
