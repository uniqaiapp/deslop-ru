<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/banner-light.svg">
  <img alt="deslop-ru: Remove AI slop from Russian text" src="assets/banner.svg" width="1280" height="320">
</picture>

<h1>deslop-ru: 러시아어 텍스트의 AI 티 지우기</h1>

[![License: MIT](https://img.shields.io/badge/license-MIT-d1fe17?style=flat-square&labelColor=0d0f12)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude_Code-skill-d1fe17?style=flat-square&labelColor=0d0f12)](#설치)
[![Cursor](https://img.shields.io/badge/Cursor-rules-d1fe17?style=flat-square&labelColor=0d0f12)](#설치)
[![Codex](https://img.shields.io/badge/Codex-AGENTS.md-d1fe17?style=flat-square&labelColor=0d0f12)](#설치)
[![UniqAI](https://img.shields.io/badge/made_by-UniqAI-fdfc07?style=flat-square&labelColor=0d0f12)](https://uniqai.app/?utm_source=github&utm_medium=readme-ko&utm_campaign=deslop-ru)

**러시아어 글에서 "AI가 쓴 티"가 나게 만드는 표현을 찾아내고 고쳐 씁니다.**

[빠른 시작](#빠른-시작) · [동작 방식](#동작-방식) · [패턴 카테고리](#패턴-카테고리) · [예시](#예시) · [설치](#설치) · [자주 묻는 질문](#자주-묻는-질문)

</div>

[English](README.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português (BR)](README.pt-BR.md) · [日本語](README.ja.md) · 한국어

deslop-ru는 러시아어 텍스트에서 AI 특유의 상투적 표현(AI slop)을 걷어내는 도구입니다. Claude Code, Cursor, Codex용 스킬이면서, 의존성 없는 Python 검사기를 함께 제공합니다. 검사기는 10개 카테고리의 119개 패턴(러시아어 85개, 영어 34개)과 7가지 구조 검사로 해당 위치를 줄 번호와 함께 표시하고 점수를 매깁니다. 러시아어로 문서를 쓰는 편집자, SNS 담당자, Telegram 채널 운영자, 학생, 개발자가 글을 내보내기 전에 초안을 검사하거나 자기 목소리 그대로 고쳐 쓰는 데 쓰라고 만들었습니다.

| **줄 번호가 붙는 검사기** | **내 목소리를 지키는 재작성** | **모델 없이 하는 안전한 삭제** |
|:---|:---|:---|
| `scripts/deslop.py`는 검출된 항목마다 카테고리, 해당 구절, 수정 힌트를 출력하고 마지막에 0–100 점수를 보여줍니다. CI용 종료 코드도 반환합니다. | 스킬은 카테고리별로 고쳐 쓰고(관공서 문체, 영어 직역, 과장 표현, 알맹이 없는 도입과 마무리) 무엇을 바꿨는지 나열합니다. 사실, 숫자, 문체는 그대로 둡니다. | `strip` 모드는 지워도 의미가 바뀌지 않는 36개 구절만 삭제하고 대소문자를 바로잡습니다. |

## 빠른 시작

```bash
git clone https://github.com/uniqaiapp/deslop-ru
python3 deslop-ru/scripts/deslop.py check deslop-ru/examples/telegram-post.before.md
```

검출된 줄마다 카테고리와 한 줄짜리 수정안이 표시되고 마지막에 점수가 나옵니다. 직접 쓴 텍스트는 `python3 scripts/deslop.py check -`로 stdin에 넘기면 됩니다.

## 데모

<img alt="deslop-ru demo: the checker on a Telegram post before and after the rewrite, 100/100 down to 0/100" src="assets/demo.svg" width="820">

## 동작 방식

1. **측정.** `check`는 텍스트에 119개 정규식을 적용하고(ё는 е로 정규화, 러시아어 형태 변화는 어간으로 처리), 형식에 대해 7가지 구조 검사를 합니다. 글머리 기호로 쓴 이모지, 대시 밀도, 모든 항목에 붙은 굵은 라벨, 목록 벽, 느낌표, 제목 안의 이모지, 길이가 똑같은 문단입니다. 검출마다 1~3의 가중치가 붙습니다.
2. **채점.** `점수 = 8 × 100단어당 가중 검출 수`, 최대 100입니다. 구간은 10 미만 깨끗함, 10–29 가벼움, 30–59 심함, 60 이상은 봇이 쓴 글처럼 읽힙니다. 이 구간은 이 저장소의 약속이지 외부 지표가 아니며, 40단어 미만에서는 밀도 검사를 건너뜁니다.
3. **삭제.** `strip`은 안전한 삭제로 표시된 36개 패턴을 제거하고(`Важно отметить, что X` → `X`) 첫 글자를 다시 대문자로 만듭니다. 사실은 절대 건드리지 않습니다.
4. **재작성.** 그다음부터는 [`SKILL.md`](SKILL.md)의 스킬이 카테고리별로 이어받습니다. 동사에서 파생된 명사는 다시 동사로, 과장 형용사는 그 뒤에 숨은 사실로 바꾸거나 삭제, 세 개 나열은 하나로, 아무 말도 하지 않는 도입과 마무리는 제거합니다. 깨끗해진 텍스트와 짧은 변경 목록을 돌려줍니다.
5. **감사 모드**는 고쳐 쓰지 않고 보고만 합니다. 카테고리별 표, 형식 지표, 가장 먼저 고칠 다섯 가지입니다.

위의 숫자는 모두 `python3 scripts/deslop.py stats`가 출력한 값입니다. 이 README가 스크립트와 어긋나면 테스트가 실패합니다.

```
scripts/deslop.py check  file.md     hits + score          exit 1 with --fail-over N
scripts/deslop.py audit  file.md     breakdown + verdict   --json for machines
scripts/deslop.py strip  file.md     safe cuts only        --in-place to write back
scripts/deslop.py stats              pattern counts
```

## 패턴 카테고리

| 카테고리 | 잡아내는 것 | 예 |
|---|---|---|
| `intro` | 아무 내용도 없는 서두 | в современном мире, давайте разберёмся, не секрет, что |
| `filler` | 보여주는 대신 약속만 하는 연결어 | важно отметить, безусловно, таким образом |
| `bureau` | 관공서 문체(канцелярит) | данный, осуществлять, в рамках, является, функционал |
| `calque` | 영어 마케팅 표현의 직역 | погрузимся, на новый уровень, это не просто X, а Y, бесшовный |
| `hype` | 사실 대신 평가 | уникальный, идеально подходит, широкий спектр, максимально удобно |
| `triplet` | 형용사나 명사 세 개 연속 | быстрый, удобный и надёжный |
| `outro` | 본문을 되풀이하는 결론 | подводя итог, надеюсь, было полезно, выбор за вами |
| `chat` | 어시스턴트 대화의 흔적 | Конечно!, вот несколько советов:, надеюсь, это поможет |
| `rhetoric` | 문단 하나 걸러 나오는 버릇 | знаете ли вы, спойлер:, и вот почему, звучит знакомо? |
| `structure` | 구절이 아니라 형식 | 이모지 글머리 기호, 목록 벽, 문장마다 대시, 항목마다 굵은 라벨 |

id, 수정 힌트, 가중치가 모두 들어간 전체 표는 스크립트에서 생성되는 [`references/patterns.md`](references/patterns.md)에 있습니다. 영어 세트는 같은 카테고리를 34개 패턴으로 다룹니다(`delve`, `testament to`, `it's not just X, it's Y`, `navigate the landscape`).

## 예시

[`examples/`](examples/README.md)에 before/after 쌍 여섯 개가 있습니다. "after" 텍스트는 사람이 직접 고쳐 쓴 것이고, `examples/reports/`의 보고서는 검사기의 실제 출력이며 테스트가 바이트 단위로 재현합니다.

| 예시 | Before | After |
|---|---|---|
| Telegram 게시글, 커피 로스터리: `examples/telegram-post.before.md` | 100/100 | 0/100 |
| 상품 상세, 백팩: `examples/product-card.before.md` | 100/100 | 0/100 |
| 블로그 도입부, 미루는 습관: `examples/blog-intro.before.md` | 100/100 | 0/100 |
| 챗 답변을 기사로 붙여넣은 글: `examples/chat-answer.before.md` | 100/100 | 0/100 |
| 릴리스 노트, 대체로 괜찮음: `examples/release-notes.before.md` | 39/100 | 0/100 |
| 영어 뉴스레터: `examples/newsletter.before.md` | 100/100 | 0/100 |

<details>
<summary><b>Telegram 게시글: before → after</b></summary>

**Before** (점수 100, 검출 18건. 전체 보고서는 `examples/reports/telegram-post.check.txt`)

```text
🚀 В современном мире, где всё меняется с невероятной скоростью, важно отметить,
что качественный кофе — это не просто напиток, а настоящий ритуал!

Давайте разберёмся, почему наша новая обжарка — это именно то, что вам нужно.

✅ Уникальный вкус — тщательно отобранные зёрна из Эфиопии
✅ Инновационный подход — обжарка по авторскому профилю
…
Подводя итог, можно с уверенностью сказать: это тот самый вкус, который вы искали.
```

**After** (점수 0)

```text
Новая обжарка: Эфиопия, Иргачефф, лот 14.

Зерно с кооператива в Гедео, высота 1 900 м, мытая обработка. Обжарили светло,
под фильтр: в чашке абрикос, чай и немного бергамота. В эспрессо тоже работает,
но будет кислее, чем привычная бразилия.

Пачка 250 г, зип-лок с клапаном. Лучше всего с 5-го по 30-й день после обжарки.
```

무엇이 바뀌었나: 서두가 가장 구체적인 사실(산지, 로트)이 되었고, 형용사마다 그것이 가리키던 실체(맛 노트, 고도, 가공 방식)로 바뀌었으며, 결론과 참여 유도 미끼는 사라지고, 구체적인 제안 하나만 남았습니다.

</details>

<details>
<summary><b>릴리스 노트: 가벼운 사례와 <code>strip</code>이 혼자 할 수 있는 일</b></summary>

```text
$ python3 scripts/deslop.py check --no-fix examples/release-notes.before.md
examples/release-notes.before.md: 123 слов, язык ru
  стр. 3   [filler] Важно отметить, что  <- важно отметить
  стр. 5   [calque] бесшовную  <- бесшовный (seamless)
  стр. 7   [bureau] функционал
  оценка: 39/100 (заметно); filler 1, calque 1, bureau 1
```

첫 번째 검출은 `strip`이 혼자 제거합니다(`Важно отметить, что в этой версии` → `В этой версии`). 나머지 둘은 사람이나 스킬이 필요합니다. 고치는 방법이 삭제가 아니라 다른 단어로 바꾸는 것이기 때문입니다.

</details>

<details>
<summary><b>감사 모드</b></summary>

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

전체 출력: `examples/reports/blog-intro.audit.txt`.

</details>

## 설치

지시 파일을 읽는 에이전트라면 모두 지원합니다. 쓰는 것을 고르세요. 요구 사항: Python 3.9+. 설치할 패키지는 없습니다.

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

그다음 아무 세션에서나 `/deslop-ru`를 입력하거나, 초안을 붙여넣고 «убрать ИИ-штампы»(AI 상투어를 지워 달라)라고 요청하면 됩니다. 스킬의 `description`이 트리거가 됩니다. 플러그인으로 쓰려면 uniqaiapp 마켓플레이스가 공개된 뒤 `/plugin marketplace add uniqaiapp/skills`에 이어 `/plugin install deslop-ru@uniqaiapp`을 실행합니다.

</details>

<details>
<summary><b>Cursor</b></summary>

[`.cursor/rules/deslop-ru.mdc`](.cursor/rules/deslop-ru.mdc)를 `SKILL.md`, `scripts/`, `references/`와 함께 프로젝트의 `.cursor/rules/`에 복사합니다. 규칙 파일은 `@SKILL.md`로 스킬을 포함합니다.

</details>

<details>
<summary><b>Codex / AGENTS.md를 읽는 모든 에이전트</b></summary>

`SKILL.md`, `scripts/`, `references/`를 `.agents/skills/deslop-ru/`에 복사하고 [`codex/INSTRUCTIONS.md`](codex/INSTRUCTIONS.md)의 스니펫을 자신의 `AGENTS.md`에 추가합니다. 이 저장소의 [`AGENTS.md`](AGENTS.md)가 그 형태를 보여줍니다.

</details>

<details>
<summary><b>일반 프롬프트 또는 CI</b></summary>

[`SKILL.md`](SKILL.md)를 아무 모델의 시스템 프롬프트에 붙여넣으세요. frontmatter 외에는 특정 에이전트 전용 문법이 없습니다. CI에서는 점수로 게이트를 겁니다.

```bash
python3 scripts/deslop.py check --fail-over 20 docs/*.md
```

</details>

## 자주 묻는 질문

<details>
<summary><b>점수가 0이면 사람이 썼다는 뜻인가요?</b></summary>

아닙니다. 119개 구절과 7가지 구조 검사 중 어느 것도 걸리지 않았다는 뜻입니다. 목록만 피해 간 밋밋한 글은 통과하고, «безусловно»를 즐겨 쓰는 사람이 쓴 생생한 글에는 표시가 붙습니다. 점수는 읽기를 돕는 보조 수단이지 탐지기가 아니며, 이 저장소는 탐지기를 피하려고 하지도 않습니다.

</details>

<details>
<summary><b>그냥 모델에게 "사람처럼 써 달라"고 하면 되지 않나요?</b></summary>

모델은 자기 버릇 중 어느 것을 말하는지 모르기 때문입니다. 패턴 목록이 곧 명세입니다. 검사기는 모델에게(그리고 여러분에게) 정확히 어느 줄, 어느 구절, 어느 카테고리인지 알려주고, 스킬에는 카테고리마다 그 자리에 무엇을 넣을지에 대한 규칙이 하나씩 있습니다.

</details>

<details>
<summary><b>«данные»나 «эффективность» 같은 정상적인 단어도 걸리나요?</b></summary>

«Данные»(데이터)는 «данный» 규칙에서 제외되어 있습니다. «Эффективный», «актуальный», «экосистема»는 가중치 1이며, 기술 문서에서 문제없이 쓰인 경우에도 검출됩니다. 스킬은 이런 단어를 그대로 두고 그 사실을 알리도록 지시받습니다. 어떤 규칙이 자주 오탐한다면 해당 문장을 첨부해 이슈를 열어 주세요. 정규식은 한 줄입니다.

</details>

<details>
<summary><b>영어도 되나요?</b></summary>

됩니다. 더 작은 세트(34개 패턴)와 같은 구조 검사를 씁니다. 언어는 자동 감지되고 `--lang en`으로 강제할 수도 있습니다. 영어 위주 작업에는 전용 도구가 있습니다. 이 도구가 제값을 하는 곳은 영어용 목록으로는 아무것도 잡히지 않는 러시아어 텍스트입니다.

</details>

<details>
<summary><b>이 README의 숫자는 어디서 나온 건가요?</b></summary>

패턴 수는 `python3 scripts/deslop.py stats`, 예시 점수는 `examples/reports/scores.txt`에서 나옵니다. 둘 중 하나라도 어긋나면 `python3 tests/run.py`가 실패합니다.

</details>

## 관련 프로젝트

- [token-diet](https://github.com/uniqaiapp/token-diet): 의미를 잃지 않고 프롬프트와 컨텍스트 토큰을 줄입니다. 측정 가능한 규칙, 표준 라이브러리만 쓰는 추정기, before/after 예시.
- [skill-shrinker](https://github.com/uniqaiapp/skill-shrinker): SKILL.md나 에이전트 지시 파일을 줄입니다. 크기를 재고, 긴 내용은 references로 옮기고, 트리거는 그대로 유지합니다.
- [model-router](https://github.com/uniqaiapp/model-router): 일을 해낼 수 있는 가장 저렴한 모델을 고릅니다. 규칙 표와, 작업을 유형·길이·위험도로 분배하는 표준 라이브러리 스크립트.

## 기여하기

이슈와 pull request를 환영합니다. 변경은 작게 유지하고 PR 설명에 before/after 문장을 하나 넣어 주세요.
로컬 검사(`python3 tests/run.py`, 의존성 없음)와 패턴 추가 방법은 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고하세요.

## 라이선스

[MIT](LICENSE) © UniqAI

---

<div align="center">

<sub>Made by <a href="https://uniqai.app/?utm_source=github&utm_medium=readme-ko&utm_campaign=deslop-ru">UniqAI</a>. AI 사진, 영상, 채팅을 하나로 묶은 앱입니다. uniqai.app의 러시아어 페이지도 같은 규칙으로 씁니다.</sub>

</div>
