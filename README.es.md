<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.svg">
  <img alt="deslop-ru: Remove AI slop from Russian text" src="assets/banner.svg" width="1280" height="320">
</picture>

<h1>deslop-ru: elimina el AI slop de textos en ruso</h1>

[![License: MIT](https://img.shields.io/badge/license-MIT-d1fe17?style=flat-square&labelColor=0d0f12)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-d1fe17?style=flat-square&labelColor=0d0f12)](#instalación)
[![Cursor](https://img.shields.io/badge/Cursor-rules-d1fe17?style=flat-square&labelColor=0d0f12)](#instalación)
[![Codex](https://img.shields.io/badge/Codex-AGENTS.md-d1fe17?style=flat-square&labelColor=0d0f12)](#instalación)
[![UniqAI](https://img.shields.io/badge/made_by-UniqAI-fdfc07?style=flat-square&labelColor=0d0f12)](https://uniqai.app/?utm_source=github&utm_medium=readme-es&utm_campaign=deslop-ru)

**Detecta y reescribe las frases que hacen que un texto en ruso suene a IA.**

[Inicio rápido](#inicio-rápido) · [Cómo funciona](#cómo-funciona) · [Categorías de patrones](#categorías-de-patrones) · [Ejemplos](#ejemplos) · [Instalación](#instalación) · [Preguntas frecuentes](#preguntas-frecuentes)

</div>

[English](README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · Español · [Português (BR)](README.pt-BR.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

deslop-ru elimina el AI slop (las muletillas y clichés de la IA) de textos en ruso. Es una skill para Claude Code, Cursor y Codex, más un verificador en Python sin dependencias que marca 119 patrones (85 en ruso, 34 en inglés) en 10 categorías y 7 comprobaciones de estructura, con número de línea y una puntuación. Está pensado para editores, responsables de redes sociales, autores de canales de Telegram, estudiantes y desarrolladores que escriben documentación en ruso y quieren revisar un borrador, o reescribirlo con su propia voz, antes de publicarlo.

| **Verificador con números de línea** | **Reescritura que conserva tu voz** | **Recortes seguros, sin modelo** |
|:---|:---|:---|
| `scripts/deslop.py` imprime cada coincidencia con su categoría, la frase y una pista de corrección, y después una puntuación de 0 a 100. Código de salida para CI. | La skill reescribe por categoría (lenguaje burocrático, calcos, hype, introducciones y cierres vacíos) y enumera lo que cambió. Hechos, cifras y registro se mantienen. | El modo `strip` borra solo las 36 frases cuya eliminación nunca cambia el significado y corrige las mayúsculas. |

## Inicio rápido

```bash
git clone https://github.com/uniqaiapp/deslop-ru
python3 deslop-ru/scripts/deslop.py check deslop-ru/examples/telegram-post.before.md
```

Verás cada línea marcada con su categoría y una corrección de una línea, y al final la puntuación. Para pasar tu propio texto por stdin: `python3 scripts/deslop.py check -`.

## Demo

<img alt="deslop-ru demo: the checker on a Telegram post before and after the rewrite, 100/100 down to 0/100" src="assets/demo.svg" width="820">

## Cómo funciona

1. **Medir.** `check` ejecuta 119 patrones regex sobre el texto (ё se normaliza a е, raíces para la morfología rusa) y 7 comprobaciones de estructura sobre la forma: emojis como viñetas, densidad de rayas, etiqueta en negrita en cada viñeta, muros de listas, signos de exclamación, emojis en los títulos, párrafos de longitud idéntica. Cada coincidencia tiene un peso de 1 a 3.
2. **Puntuar.** `puntuación = 8 × coincidencias ponderadas por cada 100 palabras`, con tope en 100. Rangos: menos de 10 limpio, 10–29 leve, 30–59 marcado, 60 o más suena a bot. Los rangos son una convención de este repositorio, no una medida externa; las comprobaciones de densidad se omiten por debajo de 40 palabras.
3. **Recortar.** `strip` elimina los 36 patrones marcados como recortes seguros (`Важно отметить, что X` → `X`) y vuelve a poner las mayúsculas. Nunca toca un hecho.
4. **Reescribir.** La skill de [`SKILL.md`](SKILL.md) continúa desde ahí, categoría por categoría: los sustantivos verbales vuelven a ser verbos, los adjetivos de hype se sustituyen por el hecho que ocultan o se eliminan, las tríadas se reducen a un solo elemento, las introducciones y cierres que no dicen nada desaparecen. Devuelve el texto limpio más una lista breve de lo que cambió.
5. **Modo auditoría**: informa sin reescribir: tabla por categorías, métricas de forma, las cinco correcciones por las que empezar.

Todas las cifras anteriores salen de `python3 scripts/deslop.py stats`; las pruebas fallan si este README se desvía del script.

```
scripts/deslop.py check  file.md     hits + score          exit 1 with --fail-over N
scripts/deslop.py audit  file.md     breakdown + verdict   --json for machines
scripts/deslop.py strip  file.md     safe cuts only        --in-place to write back
scripts/deslop.py stats              pattern counts
```

## Categorías de patrones

| Categoría | Qué detecta | Ejemplo |
|---|---|---|
| `intro` | Aperturas que no dicen nada | в современном мире, давайте разберёмся, не секрет, что |
| `filler` | Conectores que prometen en vez de mostrar | важно отметить, безусловно, таким образом |
| `bureau` | Lenguaje burocrático (канцелярит) | данный, осуществлять, в рамках, является, функционал |
| `calque` | Calcos del marketing en inglés | погрузимся, на новый уровень, это не просто X, а Y, бесшовный |
| `hype` | Valoración en lugar de hecho | уникальный, идеально подходит, широкий спектр, максимально удобно |
| `triplet` | Tres adjetivos o sustantivos seguidos | быстрый, удобный и надёжный |
| `outro` | Conclusiones que repiten el texto | подводя итог, надеюсь, было полезно, выбор за вами |
| `chat` | Restos de conversación con el asistente | Конечно!, вот несколько советов:, надеюсь, это поможет |
| `rhetoric` | Tics colocados cada dos párrafos | знаете ли вы, спойлер:, и вот почему, звучит знакомо? |
| `structure` | Forma, no frases | emojis como viñetas, muros de listas, una raya en cada oración, etiqueta en negrita por viñeta |

La tabla completa con ids, pistas de corrección y pesos está en [`references/patterns.md`](references/patterns.md), generada a partir del script. El conjunto en inglés cubre las mismas categorías con 34 patrones (`delve`, `testament to`, `it's not just X, it's Y`, `navigate the landscape`).

## Ejemplos

Seis pares antes/después en [`examples/`](examples/README.md). Los textos «después» son reescrituras hechas a mano; los informes de `examples/reports/` son la salida real del verificador y las pruebas los reproducen byte a byte.

| Ejemplo | Antes | Después |
|---|---|---|
| Post de Telegram, tostador de café: `examples/telegram-post.before.md` | 100/100 | 0/100 |
| Ficha de producto, mochila: `examples/product-card.before.md` | 100/100 | 0/100 |
| Introducción de blog, procrastinación: `examples/blog-intro.before.md` | 100/100 | 0/100 |
| Respuesta de chat pegada como artículo: `examples/chat-answer.before.md` | 100/100 | 0/100 |
| Notas de versión, casi limpias: `examples/release-notes.before.md` | 39/100 | 0/100 |
| Newsletter en inglés: `examples/newsletter.before.md` | 100/100 | 0/100 |

<details>
<summary><b>Post de Telegram: antes → después</b></summary>

**Antes** (puntuación 100, 18 coincidencias; informe completo en `examples/reports/telegram-post.check.txt`)

```text
🚀 В современном мире, где всё меняется с невероятной скоростью, важно отметить,
что качественный кофе — это не просто напиток, а настоящий ритуал!

Давайте разберёмся, почему наша новая обжарка — это именно то, что вам нужно.

✅ Уникальный вкус — тщательно отобранные зёрна из Эфиопии
✅ Инновационный подход — обжарка по авторскому профилю
…
Подводя итог, можно с уверенностью сказать: это тот самый вкус, который вы искали.
```

**Después** (puntuación 0)

```text
Новая обжарка: Эфиопия, Иргачефф, лот 14.

Зерно с кооператива в Гедео, высота 1 900 м, мытая обработка. Обжарили светло,
под фильтр: в чашке абрикос, чай и немного бергамота. В эспрессо тоже работает,
но будет кислее, чем привычная бразилия.

Пачка 250 г, зип-лок с клапаном. Лучше всего с 5-го по 30-й день после обжарки.
```

Qué cambió: la apertura pasó a ser el hecho más concreto (origen, lote); cada adjetivo se convirtió en aquello que representaba (notas de cata, altitud, proceso); la conclusión y el cebo de interacción desaparecieron; se mantuvo una única oferta concreta.

</details>

<details>
<summary><b>Notas de versión: un caso leve y lo que <code>strip</code> hace por sí solo</b></summary>

```text
$ python3 scripts/deslop.py check --no-fix examples/release-notes.before.md
examples/release-notes.before.md: 123 слов, язык ru
  стр. 3   [filler] Важно отметить, что  <- важно отметить
  стр. 5   [calque] бесшовную  <- бесшовный (seamless)
  стр. 7   [bureau] функционал
  оценка: 39/100 (заметно); filler 1, calque 1, bureau 1
```

`strip` elimina la primera coincidencia por sí solo (`Важно отметить, что в этой версии` → `В этой версии`); las otras dos necesitan a una persona o a la skill, porque la corrección es otra palabra, no una eliminación.

</details>

<details>
<summary><b>Modo auditoría</b></summary>

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

Salida completa: `examples/reports/blog-intro.audit.txt`.

</details>

## Instalación

Funciona con cualquier agente que lea archivos de instrucciones. Elige el tuyo. Requisitos: Python 3.9+. No hay paquetes que instalar.

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

Después escribe `/deslop-ru` en cualquier sesión, o simplemente pega un borrador y pide «убрать ИИ-штампы» (quitar los clichés de IA); la `description` de la skill la activa. Como plugin, cuando se publique el marketplace de uniqaiapp: `/plugin marketplace add uniqaiapp/skills` y luego `/plugin install deslop-ru@uniqaiapp`.

</details>

<details>
<summary><b>Cursor</b></summary>

Copia [`.cursor/rules/deslop-ru.mdc`](.cursor/rules/deslop-ru.mdc) en el `.cursor/rules/` de tu proyecto, junto con `SKILL.md`, `scripts/` y `references/`. La regla incrusta la skill con `@SKILL.md`.

</details>

<details>
<summary><b>Codex / cualquier agente con AGENTS.md</b></summary>

Copia `SKILL.md`, `scripts/` y `references/` en `.agents/skills/deslop-ru/` y añade el fragmento de [`codex/INSTRUCTIONS.md`](codex/INSTRUCTIONS.md) a tu `AGENTS.md`. El propio [`AGENTS.md`](AGENTS.md) de este repositorio muestra la forma.

</details>

<details>
<summary><b>Prompt plano o CI</b></summary>

Pega [`SKILL.md`](SKILL.md) en el system prompt de cualquier modelo; no tiene sintaxis específica de ningún agente fuera del frontmatter. Para CI, pon un umbral sobre la puntuación:

```bash
python3 scripts/deslop.py check --fail-over 20 docs/*.md
```

</details>

## Preguntas frecuentes

<details>
<summary><b>¿Una puntuación de 0 significa que lo escribió una persona?</b></summary>

No. Significa que ninguna de las 119 frases ni de las 7 comprobaciones de forma se activó. Un texto insípido que esquiva la lista pasa; un texto vivo de alguien a quien le gusta «безусловно» recibe marcas. La puntuación es una ayuda de lectura, no un detector, y el repositorio tampoco intenta burlar detectores.

</details>

<details>
<summary><b>¿Por qué no pedirle al modelo que «escriba como un humano» y ya?</b></summary>

Porque el modelo no sabe a cuáles de sus hábitos te refieres. La lista de patrones es la especificación: el verificador le dice al modelo (y a ti) exactamente qué línea, qué frase y qué categoría, y la skill tiene una regla por categoría sobre qué poner en su lugar.

</details>

<details>
<summary><b>¿Marcará palabras legítimas como «данные» o «эффективность»?</b></summary>

«Данные» (datos) está excluida de la regla de «данный». «Эффективный», «актуальный» y «экосистема» tienen peso 1 y sí se marcan en textos técnicos donde son correctas; la skill tiene instrucciones de dejarlas y decirlo. Si una regla falla a menudo, abre un issue con la frase; la regex es una sola línea.

</details>

<details>
<summary><b>¿Y en inglés?</b></summary>

Sí, con un conjunto más pequeño (34 patrones) y las mismas comprobaciones de estructura; el idioma se detecta automáticamente o se fuerza con `--lang en`. Para trabajar principalmente en inglés hay herramientas dedicadas; esta se gana su lugar con el texto en ruso, donde las listas en inglés no detectan nada.

</details>

<details>
<summary><b>¿De dónde salen las cifras de este README?</b></summary>

De `python3 scripts/deslop.py stats` para el número de patrones y de `examples/reports/scores.txt` para las puntuaciones de los ejemplos. `python3 tests/run.py` falla si cualquiera de los dos se desvía.

</details>

## Proyectos relacionados

- [token-diet](https://github.com/uniqaiapp/token-diet): reduce los tokens del prompt y del contexto sin perder significado: reglas medibles, un estimador en stdlib y ejemplos antes/después.
- [skill-shrinker](https://github.com/uniqaiapp/skill-shrinker): comprime cualquier SKILL.md o archivo de instrucciones de agente: mide el tamaño, mueve el material largo a referencias y mantiene intactos los disparadores.
- [model-router](https://github.com/uniqaiapp/model-router): elige el modelo más barato capaz de hacer el trabajo: una tabla de reglas y un script en stdlib que enruta tareas por tipo, longitud y riesgo.

## Contribuir

Los issues y pull requests son bienvenidos. Mantén los cambios pequeños e incluye una oración antes/después en la descripción del PR.
Consulta [CONTRIBUTING.md](CONTRIBUTING.md) para las comprobaciones locales (`python3 tests/run.py`, sin dependencias) y para saber cómo añadir un patrón.

## Licencia

[MIT](LICENSE) © UniqAI

---

<div align="center">

<sub>Made by <a href="https://uniqai.app/?utm_source=github&utm_medium=readme-es&utm_campaign=deslop-ru">UniqAI</a>, una app de fotos, video y chat con IA. Las páginas en ruso de uniqai.app están escritas con estas mismas reglas.</sub>

</div>
