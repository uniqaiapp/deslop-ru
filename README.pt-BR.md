<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.svg">
  <img alt="deslop-ru: Remove AI slop from Russian text" src="assets/banner.svg" width="1280" height="320">
</picture>

<h1>deslop-ru: remova o AI slop de textos em russo</h1>

[![License: MIT](https://img.shields.io/badge/license-MIT-d1fe17?style=flat-square&labelColor=0d0f12)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-d1fe17?style=flat-square&labelColor=0d0f12)](#instalação)
[![Cursor](https://img.shields.io/badge/Cursor-rules-d1fe17?style=flat-square&labelColor=0d0f12)](#instalação)
[![Codex](https://img.shields.io/badge/Codex-AGENTS.md-d1fe17?style=flat-square&labelColor=0d0f12)](#instalação)
[![UniqAI](https://img.shields.io/badge/made_by-UniqAI-fdfc07?style=flat-square&labelColor=0d0f12)](https://uniqai.app/?utm_source=github&utm_medium=readme-pt-br&utm_campaign=deslop-ru)

**Encontra e reescreve as frases que dão cara de IA a um texto em russo.**

[Início rápido](#início-rápido) · [Como funciona](#como-funciona) · [Categorias de padrões](#categorias-de-padrões) · [Exemplos](#exemplos) · [Instalação](#instalação) · [Perguntas frequentes](#perguntas-frequentes)

</div>

[English](README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · Português (BR) · [日本語](README.ja.md) · [한국어](README.ko.md)

O deslop-ru remove o AI slop (os clichês e muletas de texto gerado por IA) de textos em russo. É uma skill para Claude Code, Cursor e Codex, mais um verificador em Python sem dependências que sinaliza 119 padrões (85 em russo, 34 em inglês) em 10 categorias e 7 verificações de estrutura, com número de linha e uma nota. Serve para editores, gerentes de redes sociais, autores de canais no Telegram, estudantes e desenvolvedores que escrevem documentação em russo e querem revisar um rascunho, ou reescrevê-lo com a própria voz, antes de publicar.

| **Verificador com números de linha** | **Reescrita que mantém a sua voz** | **Cortes seguros, sem modelo** |
|:---|:---|:---|
| `scripts/deslop.py` imprime cada ocorrência com categoria, frase e uma dica de correção, e depois uma nota de 0 a 100. Código de saída para CI. | A skill reescreve por categoria (burocratês, decalques, hype, aberturas e fechamentos vazios) e lista o que mudou. Fatos, números e registro ficam como estavam. | O modo `strip` apaga apenas as 36 frases cuja remoção nunca muda o sentido e corrige as maiúsculas. |

## Início rápido

```bash
git clone https://github.com/uniqaiapp/deslop-ru
python3 deslop-ru/scripts/deslop.py check deslop-ru/examples/telegram-post.before.md
```

Você vê cada linha sinalizada com a categoria e uma correção de uma linha, e no fim a nota. Para passar o seu próprio texto pelo stdin: `python3 scripts/deslop.py check -`.

## Demonstração

<img alt="deslop-ru demo: the checker on a Telegram post before and after the rewrite, 100/100 down to 0/100" src="assets/demo.svg" width="820">

## Como funciona

1. **Medir.** O `check` roda 119 padrões regex sobre o texto (ё normalizado para е, radicais para a morfologia russa) e 7 verificações de estrutura sobre a forma: emoji como marcador de lista, densidade de travessões, rótulo em negrito em todo item, paredões de lista, pontos de exclamação, emoji em títulos, parágrafos do mesmo tamanho. Cada ocorrência tem peso de 1 a 3.
2. **Pontuar.** `nota = 8 × ocorrências ponderadas por 100 palavras`, com teto em 100. Faixas: abaixo de 10 limpo, 10–29 leve, 30–59 pesado, 60 ou mais parece bot. As faixas são uma convenção deste repositório, não uma medida externa; as verificações de densidade são puladas abaixo de 40 palavras.
3. **Cortar.** O `strip` remove os 36 padrões marcados como cortes seguros (`Важно отметить, что X` → `X`) e refaz as maiúsculas. Nunca mexe em um fato.
4. **Reescrever.** A skill em [`SKILL.md`](SKILL.md) continua dali, categoria por categoria: substantivos verbais voltam a ser verbos, adjetivos de hype dão lugar ao fato por trás deles ou somem, trincas viram um item só, aberturas e fechamentos que não dizem nada são removidos. Ela devolve o texto limpo mais uma lista curta do que mudou.
5. **Modo auditoria** relata sem reescrever: tabela por categoria, métricas de forma, as cinco correções para fazer primeiro.

Todos os números acima vêm de `python3 scripts/deslop.py stats`; os testes falham se este README divergir do script.

```
scripts/deslop.py check  file.md     hits + score          exit 1 with --fail-over N
scripts/deslop.py audit  file.md     breakdown + verdict   --json for machines
scripts/deslop.py strip  file.md     safe cuts only        --in-place to write back
scripts/deslop.py stats              pattern counts
```

## Categorias de padrões

| Categoria | O que pega | Exemplo |
|---|---|---|
| `intro` | Aberturas que não dizem nada | в современном мире, давайте разберёмся, не секрет, что |
| `filler` | Conectivos que prometem em vez de mostrar | важно отметить, безусловно, таким образом |
| `bureau` | Burocratês (канцелярит) | данный, осуществлять, в рамках, является, функционал |
| `calque` | Decalques do marketing em inglês | погрузимся, на новый уровень, это не просто X, а Y, бесшовный |
| `hype` | Avaliação no lugar de fato | уникальный, идеально подходит, широкий спектр, максимально удобно |
| `triplet` | Três adjetivos ou substantivos em sequência | быстрый, удобный и надёжный |
| `outro` | Conclusões que repetem o texto | подводя итог, надеюсь, было полезно, выбор за вами |
| `chat` | Resíduos de conversa com o assistente | Конечно!, вот несколько советов:, надеюсь, это поможет |
| `rhetoric` | Cacoetes colocados a cada dois parágrafos | знаете ли вы, спойлер:, и вот почему, звучит знакомо? |
| `structure` | Forma, não frases | emoji como marcador, paredões de lista, um travessão em cada frase, rótulo em negrito por item |

A tabela completa com ids, dicas de correção e pesos está em [`references/patterns.md`](references/patterns.md), gerada a partir do script. O conjunto em inglês cobre as mesmas categorias com 34 padrões (`delve`, `testament to`, `it's not just X, it's Y`, `navigate the landscape`).

## Exemplos

Seis pares antes/depois em [`examples/`](examples/README.md). Os textos "depois" são reescritas feitas à mão; os relatórios em `examples/reports/` são a saída real do verificador e os testes os reproduzem byte a byte.

| Exemplo | Antes | Depois |
|---|---|---|
| Post no Telegram, torrefação de café: `examples/telegram-post.before.md` | 100/100 | 0/100 |
| Página de produto, mochila: `examples/product-card.before.md` | 100/100 | 0/100 |
| Introdução de blog, procrastinação: `examples/blog-intro.before.md` | 100/100 | 0/100 |
| Resposta de chat colada como artigo: `examples/chat-answer.before.md` | 100/100 | 0/100 |
| Release notes, quase limpas: `examples/release-notes.before.md` | 39/100 | 0/100 |
| Newsletter em inglês: `examples/newsletter.before.md` | 100/100 | 0/100 |

<details>
<summary><b>Post no Telegram: antes → depois</b></summary>

**Antes** (nota 100, 18 ocorrências; relatório completo em `examples/reports/telegram-post.check.txt`)

```text
🚀 В современном мире, где всё меняется с невероятной скоростью, важно отметить,
что качественный кофе — это не просто напиток, а настоящий ритуал!

Давайте разберёмся, почему наша новая обжарка — это именно то, что вам нужно.

✅ Уникальный вкус — тщательно отобранные зёрна из Эфиопии
✅ Инновационный подход — обжарка по авторскому профилю
…
Подводя итог, можно с уверенностью сказать: это тот самый вкус, который вы искали.
```

**Depois** (nota 0)

```text
Новая обжарка: Эфиопия, Иргачефф, лот 14.

Зерно с кооператива в Гедео, высота 1 900 м, мытая обработка. Обжарили светло,
под фильтр: в чашке абрикос, чай и немного бергамота. В эспрессо тоже работает,
но будет кислее, чем привычная бразилия.

Пачка 250 г, зип-лок с клапаном. Лучше всего с 5-го по 30-й день после обжарки.
```

O que mudou: a abertura virou o fato mais concreto (origem, lote); cada adjetivo virou aquilo que ele representava (notas de sabor, altitude, processo); a conclusão e a isca de engajamento saíram; uma oferta concreta ficou.

</details>

<details>
<summary><b>Release notes: um caso leve e o que o <code>strip</code> faz sozinho</b></summary>

```text
$ python3 scripts/deslop.py check --no-fix examples/release-notes.before.md
examples/release-notes.before.md: 123 слов, язык ru
  стр. 3   [filler] Важно отметить, что  <- важно отметить
  стр. 5   [calque] бесшовную  <- бесшовный (seamless)
  стр. 7   [bureau] функционал
  оценка: 39/100 (заметно); filler 1, calque 1, bureau 1
```

O `strip` remove a primeira ocorrência sozinho (`Важно отметить, что в этой версии` → `В этой версии`); as outras duas precisam de uma pessoa ou da skill, porque a correção é outra palavra, não uma remoção.

</details>

<details>
<summary><b>Modo auditoria</b></summary>

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

Saída completa: `examples/reports/blog-intro.audit.txt`.

</details>

## Instalação

Funciona com qualquer agente que leia arquivos de instruções. Escolha o seu. Requisitos: Python 3.9+. Nenhum pacote para instalar.

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

Depois, `/deslop-ru` em qualquer sessão, ou simplesmente cole um rascunho e peça «убрать ИИ-штампы» (tirar os clichês de IA); a `description` da skill a aciona. Como plugin, quando o marketplace da uniqaiapp for publicado: `/plugin marketplace add uniqaiapp/skills` e então `/plugin install deslop-ru@uniqaiapp`.

</details>

<details>
<summary><b>Cursor</b></summary>

Copie [`.cursor/rules/deslop-ru.mdc`](.cursor/rules/deslop-ru.mdc) para o `.cursor/rules/` do seu projeto, junto com `SKILL.md`, `scripts/` e `references/`. A regra embute a skill com `@SKILL.md`.

</details>

<details>
<summary><b>Codex / qualquer agente com AGENTS.md</b></summary>

Copie `SKILL.md`, `scripts/` e `references/` para `.agents/skills/deslop-ru/` e adicione o trecho de [`codex/INSTRUCTIONS.md`](codex/INSTRUCTIONS.md) ao seu `AGENTS.md`. O próprio [`AGENTS.md`](AGENTS.md) deste repositório mostra o formato.

</details>

<details>
<summary><b>Prompt puro ou CI</b></summary>

Cole o [`SKILL.md`](SKILL.md) no system prompt de qualquer modelo; ele não tem sintaxe específica de agente fora do frontmatter. Para CI, bloqueie pela nota:

```bash
python3 scripts/deslop.py check --fail-over 20 docs/*.md
```

</details>

## Perguntas frequentes

<details>
<summary><b>Nota 0 significa que foi uma pessoa que escreveu?</b></summary>

Não. Significa que nenhuma das 119 frases e das 7 verificações de forma disparou. Um texto sem graça que desvia da lista passa; um texto vivo de alguém que gosta de «безусловно» é sinalizado. A nota é um apoio de leitura, não um detector, e o repositório também não tenta enganar detectores.

</details>

<details>
<summary><b>Por que não pedir ao modelo para "escrever como humano" e pronto?</b></summary>

Porque o modelo não sabe a quais dos hábitos dele você se refere. A lista de padrões é a especificação: o verificador diz ao modelo (e a você) exatamente qual linha, qual frase, qual categoria, e a skill tem uma regra por categoria sobre o que colocar no lugar.

</details>

<details>
<summary><b>Ele vai sinalizar palavras legítimas como «данные» ou «эффективность»?</b></summary>

«Данные» (dados) está excluída da regra de «данный». «Эффективный», «актуальный» e «экосистема» têm peso 1 e são sinalizadas em texto técnico onde estão corretas; a skill é instruída a deixá-las e avisar. Se uma regra erra com frequência, abra uma issue com a frase; a regex é uma linha só.

</details>

<details>
<summary><b>E em inglês?</b></summary>

Sim, com um conjunto menor (34 padrões) e as mesmas verificações de estrutura; o idioma é detectado automaticamente ou forçado com `--lang en`. Para trabalho principalmente em inglês existem ferramentas dedicadas; esta se justifica no texto em russo, onde as listas em inglês não pegam nada.

</details>

<details>
<summary><b>De onde vêm os números deste README?</b></summary>

De `python3 scripts/deslop.py stats` para as contagens de padrões e de `examples/reports/scores.txt` para as notas dos exemplos. `python3 tests/run.py` falha se qualquer um dos dois divergir.

</details>

## Projetos relacionados

- [token-diet](https://github.com/uniqaiapp/token-diet): corta tokens de prompt e de contexto sem perder sentido: regras mensuráveis, um estimador em stdlib e exemplos antes/depois.
- [skill-shrinker](https://github.com/uniqaiapp/skill-shrinker): encolhe qualquer SKILL.md ou arquivo de instruções de agente: mede o tamanho, move o material longo para referências e mantém os gatilhos intactos.
- [model-router](https://github.com/uniqaiapp/model-router): escolhe o modelo mais barato que dá conta da tarefa: uma tabela de regras e um script em stdlib que roteia tarefas por tipo, tamanho e risco.

## Como contribuir

Issues e pull requests são bem-vindos. Mantenha as mudanças pequenas e inclua uma frase antes/depois na descrição do PR.
Veja [CONTRIBUTING.md](CONTRIBUTING.md) para as verificações locais (`python3 tests/run.py`, sem dependências) e para saber como adicionar um padrão.

## Licença

[MIT](LICENSE) © UniqAI

---

<div align="center">

<sub>Made by <a href="https://uniqai.app/?utm_source=github&utm_medium=readme-pt-br&utm_campaign=deslop-ru">UniqAI</a>, um app de foto, vídeo e chat com IA. As páginas em russo do uniqai.app são escritas com as mesmas regras.</sub>

</div>
