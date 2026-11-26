#!/usr/bin/env python3
"""Build the GitHub Pages site (docs/) from examples/ and scripts/deslop.py. Stdlib only.

    python3 scripts/site.py          # writes docs/
    python3 scripts/site.py --check  # exits 1 if docs/ is out of date

Every number on the site comes from deslop.py, so the site, the CLI and the committed examples cannot disagree.
The in-browser checker (site/checker.js) is a port of that code; tests/test_site.py runs both over every example and
a set of edge texts and fails on any difference. Static assets live in site/ and are copied as is.
"""
import html
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("deslop", os.path.join(ROOT, "scripts", "deslop.py"))
D = importlib.util.module_from_spec(_spec)
sys.modules["deslop"] = D
_spec.loader.exec_module(D)

OUT = os.path.join(ROOT, "docs")
STATIC = os.path.join(ROOT, "site")

BASE = "https://uniqaiapp.github.io/deslop-ru/"
REPO = "https://github.com/uniqaiapp/deslop-ru"
HUB = "https://uniqaiapp.github.io/"
UNIQ = "https://" + "uniqai.app"
CAMPAIGN = "deslop-ru"
SITE_UPDATED = "2026-11-26"  # fixed so the output is deterministic; bump when the site content changes
OG_IMAGE = BASE + "assets/social-preview.png"
OG_SIZE = (1280, 640)
POSTHOG_KEY = "phc_AVmhcac2jVRwi9asHEuhzJXnAbQA2hzfUxzWvzjyLPc8"  # public project key (EU), same as uniqai.app
LINKEDIN = "https://www.linkedin.com/in/vlad-yasinski-ua5er/"
ROIMOBI = "https://www.roimobi.com/?utm_source=github&utm_medium=pages&utm_campaign=" + CAMPAIGN
AUTHOR = {"@type": "Person", "name": "Vlad Yasinski", "url": "https://www.roimobi.com/",
          "sameAs": ["https://www.roimobi.com", LINKEDIN, "https://github.com/ua5er"]}
SUFFIX = " | deslop-ru"
INDEXNOW_KEY = "5244c612e705bf8bf4865cab7ec56be1"

LIVE_TOOLS = {"awesome-ai-video-prompts", "video-director", "ugc-ad-director", "no-plastic"}  # have a working GitHub Pages site
TOOLS = [
    ("no-plastic", "Проверка промптов для портретов", "Ищет слова, из-за которых ИИ-портрет выглядит пластиковым, и подсказывает, чем их заменить."),
    ("awesome-ai-video-prompts", "Галерея промптов для видео", "Промпты для ИИ-видео с настройками моделей."),
    ("video-director", "Раскадровка для ИИ-видео", "Планы по тактам на входе, готовые промпты для Kling, Veo и других на выходе."),
    ("ugc-ad-director", "Проверка сценария UGC-рекламы", "Проверяет сценарий ролика и выдаёт промпты по планам."),
    ("ai-video-pricing", "Цены на ИИ-видео", "Цена за секунду и за ролик у разных моделей, у каждой строки источник и дата."),
    ("suno-producer", "Продюсер песен для Suno", "Структура, теги и строка стиля для песен в Suno."),
]

PRIVACY = ("Текст остаётся в браузере и никуда не отправляется. Страница считает только анонимные просмотры, нажатия кнопок "
           "и уровень результата, но не сами слова.")

N_PAT = len(D.PATTERNS)
N_RU = sum(1 for p in D.PATTERNS if p["lang"] == "ru")
N_EN = sum(1 for p in D.PATTERNS if p["lang"] == "en")
N_CUT = sum(1 for p in D.PATTERNS if p["cut"])
N_CAT = len(D.CATEGORIES)

STRUCT = [  # form checks from structure_checks(); text is Russian, rules mirror the code
    ("structure.emoji", "эмодзи вместо структуры", "2 и больше эмодзи на 100 слов (от 40 слов) или три строки, которые начинаются с эмодзи", 2),
    ("structure.dashes", "тире через слово", "2,5 и больше тире на 100 слов (от 40 слов)", 2),
    ("structure.bold_leads", "жирный заголовок в каждом пункте", "три и больше пунктов с жирной подписью в начале", 2),
    ("structure.list_wall", "простыня списка", "семь и больше строк списка подряд", 2),
    ("structure.exclamations", "восклицательные знаки", "2 и больше на 100 слов (от 40 слов)", 1),
    ("structure.heading_emoji", "эмодзи в заголовках", "хотя бы один заголовок с эмодзи", 1),
    ("structure.uniform_paragraphs", "абзацы одинаковой длины", "четыре и больше абзацев, длина которых почти не отличается", 1),
]

UI = {
    "scoreWord": "Оценка ", "meter": "Оценка текста",
    "level": ["Ни одного заметного штампа. Это не доказывает, что писал человек, но придраться к тексту нечему.",
              "Лёгкий налёт: пара фраз, которые стоит убрать.",
              "Заметно: читатель заподозрит генерацию. Перепишите отмеченные места.",
              "Текст читается как бот. Лучше переписать целиком, чем править точечно."],
    "markedH": "Где найдено", "hitsH": "Что найдено и что делать", "hintsH": "Подсказки для правки",
    "hintsTitle": "Оценка {s}/100, {v}", "line": "строка {l}", "weight": "вес {w}",
    "copyHints": "Скопировать подсказки", "copyClean": "Скопировать вычищенный текст",
    "noHits": "Совпадений нет. Ни одна из фраз и проверок формы не сработала.",
    "cleanH": "Безопасная вычистка", "cleanN": "Убрано {n} {f}. Остальное придётся переписать.",
    "cleanNone": "Автоматически убирать нечего: удаляемые без потери смысла фразы не найдены.",
    "cta": {"text": "Нужна помощь с переписыванием? Вставьте отмеченные места в чат UniqAI и попросите переформулировать.",
            "label": "Открыть чат UniqAI", "href": None},
    "bar": "Оценка {s}/100 · {v} · {n}",
    "hitForms": ["находка", "находки", "находок"], "wordForms": ["слово", "слова", "слов"], "phraseForms": ["фраза", "фразы", "фраз"],
    "empty": "Вставьте текст, чтобы увидеть оценку.", "emptyBar": "Вставьте текст и нажмите «Проверить»",
    "emptyRun": "Сначала вставьте текст, потом нажмите «Проверить».",
    "loaded": "Загружен пример «{t}». Правьте его или вставьте свой текст.",
    "oldBrowser": "Браузер слишком старый для проверки на странице. Тот же чекер работает из командной строки.",
}

FAQ = [
    ("Мой текст куда-то отправляется?",
     "Нет. Проверка работает в вашем браузере, сам текст не покидает страницу. Мы считаем только анонимные просмотры, нажатия кнопок и уровень результата, но не слова, которые вы вставили."),
    ("Это детектор ИИ?",
     "Нет. Чекер ищет приёмы, по которым текст читается как сгенерированный, а не доказывает авторство. Оценка 0 не значит, что писал человек, а живой текст, где много слов-паразитов, получит отметки. Обходить детекторы чекер не помогает и не пытается."),
    ("Как считается оценка?",
     "Каждая находка имеет вес от 1 до 3. Сумма весов делится на число слов, умножается на 100 и на 8, результат не больше 100. Проверки плотности включаются от 40 слов, поэтому на двух строках оценка осторожнее."),
    ("Работает ли проверка с английским?",
     "Да. Язык определяется по буквам, и для английского текста работают %d английских шаблонов: lean, game-changer, seamless, «let's dive in» и другие. Русских шаблонов %d." % (N_EN, N_RU)),
    ("Что делает безопасная вычистка?",
     "Она удаляет только %d фраз, без которых смысл не меняется, например вводное «важно отметить», и поправляет заглавную букву. Остальное чекер только показывает: канцелярит и пустые тройки нужно переписывать." % N_CUT),
    ("Как поставить это в Claude Code, Cursor или Codex?",
     "Скопируйте репозиторий в папку скиллов Claude Code, положите правило в .cursor/rules или добавьте блок в AGENTS.md. Все три способа описаны на странице установки, скрипту нужен только Python."),
    ("Это бесплатно?",
     "Да. Репозиторий открыт под лицензией MIT, а проверка на странице бесплатная и работает без регистрации."),
]

HOME_ANSWER = ("Чтобы убрать ИИ-штампы, найдите пустые зачины, канцелярит, кальки с английского и оценочные слова и замените каждое из них фактом. "
               "Чекер ниже делает первый шаг: проверяет текст по %d шаблонам, ставит оценку от 0 до 100 и предлагает безопасную вычистку. "
               "Всё считается в вашем браузере." % N_PAT)
EXAMPLES_ANSWER = ("Хороший текст без штампов называет предмет, число и источник вместо оценок вроде «уникальный» и «инновационный». "
                   "Ниже шесть пар: текст, каким его выдаёт нейросеть, и версия с конкретикой. Обе оценки посчитаны тем же чекером, что работает на главной странице сайта, поэтому их можно проверить самому.")
PATTERNS_ANSWER = ("В каталоге %d шаблонов в %d категориях, плюс 7 проверок формы: эмодзи, тире, жирные подписи, простыни списков, восклицания, "
                   "заголовки с эмодзи и ровные абзацы. У каждого шаблона есть вес от 1 до 3 и подсказка, чем заменить фразу. Любой можно открыть по ссылке." % (N_PAT, N_CAT))
HOWTO_ANSWER = ("Скопируйте репозиторий в папку скиллов Claude Code, положите правило deslop-ru.mdc в проект Cursor или добавьте блок из codex/INSTRUCTIONS.md в AGENTS.md для Codex. "
                "Скрипту нужен только Python 3.9 и новее, ставить пакеты не надо. Потом скажите агенту убрать ИИ-штампы и укажите файл.")

EX = {  # slug -> page copy. Scores, counts and phrases never appear here; they come from the checker.
    "blog-intro": dict(
        chip="Статья для блога", card="Зачин про «эпоху цифровых технологий» и список из десяти способов превращаются в короткий рассказ от первого лица.",
        h1="Статья для блога без ИИ-штампов: до и после", core=["Статья для блога без ИИ-штампов, до и после"],
        short="статья про прокрастинацию без штампов",
        q="Как переписать статью, которую выдаёт нейросеть?",
        gist="Уберите зачин про современный мир и вывод в духе «подводя итог», а список из десяти общих советов замените двумя-тремя вещами из личного опыта с цифрами и провалами. Так текст становится личным и проверяемым.",
        why="Оригинал состоит из пустого зачина, списка с жирными подписями, тире через слово и вывода, который повторяет текст. В правке автор говорит от первого лица и называет конкретику: квартальный отчёт, последняя ночь, сорок минут вместо перерыва. Помидорный таймер и напарник попали в список того, что не сработало. Такой честный минус читатель принимает за живой текст."),
    "chat-answer": dict(
        chip="Ответ чат-бота", card="«Конечно! Вот несколько рекомендаций» превращаются в план на неделю с конкретными задачами по дням.",
        h1="Как переписать ответ чат-бота, чтобы он читался по-человечески", core=["Ответ чат-бота без штампов, до и после"],
        short="ответ чат-бота про подготовку к собеседованию",
        q="Как убрать из ответа чат-бота следы ассистента?",
        gist="Удалите приветствие и просьбу обращаться за помощью, а четыре общих совета замените планом по дням: что читать, сколько задач решить и что сказать в конце собеседования. Каждый пункт можно выполнить и проверить.",
        why="Оригинал начинается с бодрого согласия, обещает несколько рекомендаций и заканчивается просьбой не стесняться. В правке неделя расписана по дням и в числах: три метрики, десять задач в день, минута на проект. Лишнее ушло, а совет не учить ночью остался, потому что он конкретный и его можно выполнить."),
    "newsletter": dict(
        chip="Рассылка на английском", card="Письмо про game-changer и seamless integration заменяется заметкой о версии 4.2 с тремя изменениями.",
        h1="Английская рассылка без ИИ-штампов: до и после", core=["Английская рассылка без штампов, до и после"],
        short="английская рассылка о релизе без штампов",
        q="Работает ли проверка на английском тексте?",
        gist="Да, английский текст проверяется по отдельным %d шаблонам. В рассылке чекер находит game-changer, seamless и dive in, а правка называет версию, три изменения и одну известную проблему. Так письмо читается как заметка автора." % N_EN,
        why="Оригинал обещает полное переосмысление и не называет ни одной функции. Правка говорит, что именно изменилось: двусторонняя синхронизация со Slack и Linear, автоматизации по расписанию, 90 дней на дашборде. Известную проблему автор не прячет, и это самый надёжный признак живого письма."),
    "product-card": dict(
        chip="Карточка товара", card="Описание «данный рюкзак представляет собой решение» превращается в карточку на 22 литра с весом и размерами карманов.",
        h1="Карточка товара без ИИ-штампов: до и после", core=["Карточка товара без ИИ-штампов: до и после"],
        short="карточка рюкзака без канцелярита",
        q="Как написать карточку товара без канцелярита?",
        gist="Замените слова вроде «данный», «осуществляет» и «широкий спектр» числами: объём, вес, ткань, размеры карманов. Покупатель сравнивает рюкзаки по параметрам, а не по эпитетам. Каждое число можно сверить с самим товаром.",
        why="В оригинале пять пунктов с жирными подписями и ни одного числа, кроме 16 дюймов. В правке есть литры, граммы, марка ткани и молний, три цвета, срок гарантии и часы работы чата. Честная строчка про дождь и чехол убеждает лучше, чем слова о высоком качестве материалов."),
    "release-notes": dict(
        chip="Заметки о релизе", card="Единственный пример со средней оценкой: штампов мало, и их убирают, не трогая ни одного факта.",
        h1="Заметки о релизе без канцелярита и ИИ-штампов", core=["Заметки о релизе без штампов, до и после"],
        short="заметки о релизе без канцелярита",
        q="Что делать, если в тексте всего несколько штампов?",
        gist="Вычеркните вводные обороты и слова-паразиты и начните каждое предложение с факта. Цифры про экспорт и список исправленных ошибок остаются как были, поэтому правка занимает минуты, а смысл совсем не страдает.",
        why="Это хороший оригинал: конкретные цифры (10 000 строк, 4 секунды вместо 40), известная проблема в Safari и честное обещание исправить в 2.4.1. Штампов мало, поэтому оценка средняя, а не 100. Правка убирает только их и оставляет текст автора нетронутым."),
    "telegram-post": dict(
        chip="Пост в Telegram", card="Кофейный пост с эмодзи-маркерами и обещанием нового уровня превращается в короткое описание лота.",
        h1="Пост в Telegram без ИИ-штампов: до и после", core=["Пост в Telegram без ИИ-штампов, до и после"],
        short="пост про кофе без эмодзи и штампов",
        q="Как переписать пост для Telegram-канала без эмодзи и штампов?",
        gist="Уберите эмодзи вместо маркеров и вступление про ритуал, назовите лот, высоту, обработку и вкус, а скидку и способ заказа оставьте в конце одной строкой. Читатель сразу видит, что именно покупает.",
        why="Оригинал хвалит вкус, но не говорит, какой он. Правка называет кооператив в Гедео, высоту 1 900 м, мытую обработку и вкус: абрикос, чай, бергамот. Скидка и кодовое слово остаются: это единственное место, где автор оригинала уже писал конкретно."),
}
ORDER = ["blog-intro", "chat-answer", "newsletter", "product-card", "release-notes", "telegram-post"]


# ---------------------------------------------------------------- helpers

def esc(s):
    return html.escape(str(s), quote=True)


def utm(path, medium="pages", content=None):
    q = "utm_source=github&utm_medium=%s&utm_campaign=%s" % (medium, CAMPAIGN)
    if content:
        q += "&utm_content=" + content
    return UNIQ + path + ("&" if "?" in path else "?") + q


def jdump(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def ru_plural(n, forms):
    n10, n100 = n % 10, n % 100
    if n10 == 1 and n100 != 11:
        return forms[0]
    if 2 <= n10 <= 4 and not 12 <= n100 <= 14:
        return forms[1]
    return forms[2]


def fit(options, lo, hi, what):
    for o in options:
        if lo <= len(o) <= hi:
            return o
    raise SystemExit("no %s fits %d-%d characters; lengths %s\n%s" % (what, lo, hi, [len(o) for o in options], options[0]))


def fit_desc(options):
    return fit(options, 100, 150, "description")


def fit_title(cores):
    for c in cores:
        if len(c + SUFFIX) <= 60:
            return c + SUFFIX
    raise SystemExit("no title fits 60 characters: %s" % cores)


def check_answer(text, what):
    n = len(text.split())
    if not 40 <= n <= 60:
        raise SystemExit("answer for %s has %d words, need 40-60: %s" % (what, n, text))
    return text


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def pid(p):
    return p.replace(".", "-")


def load_examples():
    out = {}
    base = os.path.join(ROOT, "examples")
    for slug in ORDER:
        b = read("examples", slug + ".before.md").strip()
        a = read("examples", slug + ".after.md").strip()
        rb, ra = D.analyze(b), D.analyze(a)
        out[slug] = {"before": b, "after": a, "rb": rb, "ra": ra,
                     "report": read("examples", "reports", slug + ".check.txt"), **EX[slug]}
    files = sorted(n[:-len(".before.md")] for n in os.listdir(base) if n.endswith(".before.md"))
    if files != sorted(ORDER):
        raise SystemExit("example copy and files disagree: %s vs %s" % (files, sorted(ORDER)))
    return out


# ---------------------------------------------------------------- shared by the page and checker.js

def data_json(examples):
    ui = dict(UI)
    ui["cta"] = dict(UI["cta"], href=utm("/chat", content="result"))
    return {
        "version": D.VERSION,
        "patterns": [{"id": p["id"], "lang": p["lang"], "category": p["category"], "label": p["label"], "fix": p["fix"],
                      "weight": p["weight"], "cut": bool(p["cut"]), "re": p["regex"]} for p in D.PATTERNS],
        "rx": {"emoji": D.EMOJI_RX.pattern, "bullet": D.BULLET_RX.pattern, "boldLead": D.BOLD_LEAD_RX.pattern, "heading": D.HEADING_RX.pattern},
        "cats": {k: {"ru": v[0], "en": v[1], "desc": v[2]} for k, v in D.CATEGORIES.items()},
        "catOrder": list(D.CATEGORIES),
        "ui": ui,
        "samples": [{"slug": s, "title": b["chip"], "before": b["before"]} for s, b in examples.items()],
    }


def phrases_of(r, cat, limit=3):
    seen, out = set(), []
    for h in r["hits"]:
        if h["category"] != cat:
            continue
        t = h["text"] or h["label"]
        if t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)
    return out[:limit]


# ---------------------------------------------------------------- page chrome

def head(title, desc, path, graph, prefix):
    url = BASE + path
    return """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t}</title>
<meta name="description" content="{d}">
<link rel="canonical" href="{u}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta property="og:type" content="website">
<meta property="og:site_name" content="UniqAI open source">
<meta property="og:locale" content="ru_RU">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{u}">
<meta property="og:image" content="{img}">
<meta property="og:image:width" content="{iw}">
<meta property="og:image:height" content="{ih}">
<meta property="og:image:alt" content="deslop-ru: проверка русского текста на ИИ-штампы, до и после">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
<meta name="twitter:image" content="{img}">
<meta name="theme-color" content="#0b1113">
<link rel="icon" href="{p}assets/favicon.svg" type="image/svg+xml">
<link rel="preload" href="{p}assets/fonts/Geist-Variable.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{p}site.css">
<link rel="alternate" type="text/plain" href="{b}llms.txt" title="llms.txt">
<script type="application/ld+json">{j}</script>
</head>
""".format(t=esc(title), d=esc(desc), u=url, b=BASE, p=prefix, img=OG_IMAGE, iw=OG_SIZE[0], ih=OG_SIZE[1],
           j=jdump({"@context": "https://schema.org", "@graph": graph}))


def header(prefix, current):
    links = [("", "Проверка"), ("examples/", "Примеры"), ("patterns/", "Шаблоны"), ("how-to/", "Установка")]
    nav = "".join('<a href="{p}{h}"{c}>{l}</a>'.format(p=prefix, h=h, l=l, c=' aria-current="page"' if h == current else "")
                  for h, l in links)
    return """<header class="top"><div class="wrap top-in">
<a class="brand" href="{hub}" aria-label="Открытые инструменты UniqAI"><img src="{p}assets/wordmark.svg" alt="UniqAI" width="96" height="28"><span>open source</span></a>
<nav class="nav" aria-label="Разделы">{nav}<a href="{repo}" rel="noopener">GitHub</a></nav>
<a class="btn btn-sm" href="{cta}" data-out="header">Чат UniqAI</a>
</div></header>
""".format(p=prefix, nav=nav, repo=REPO, hub=HUB, cta=esc(utm("/chat", content="header")))


def browse_links(examples):
    out = [("", "Проверка текста"), ("examples/", "Все примеры"), ("patterns/", "Каталог шаблонов"), ("how-to/", "Установка")]
    out += [("examples/%s/" % s, b["chip"]) for s, b in examples.items()]
    return out


def footer(prefix, examples, builder=False):
    browse = "".join('<a href="{p}{h}">{l}</a>'.format(p=prefix, h=h, l=esc(l)) for h, l in browse_links(examples))
    tools = "".join(
        '<li><a href="{u}" rel="noopener"><strong>{t}</strong><span>{d}</span></a></li>'.format(
            u=HUB + n + "/" if n in LIVE_TOOLS else "https://github.com/uniqaiapp/" + n, t=esc(t), d=esc(d)) for n, t, d in TOOLS)
    scripts = '<script src="{p}site.js" defer></script>'.format(p=prefix)
    if builder:
        scripts += '\n<script src="{p}checker.js" defer></script>'.format(p=prefix)
    return """<nav class="browse wrap" aria-label="Разделы сайта"><h2>Разделы сайта</h2><p>{browse}</p></nav>
<section class="more wrap" aria-labelledby="more-h">
<h2 id="more-h">Другие бесплатные инструменты UniqAI</h2>
<ul class="tools">{tools}
<li><a href="https://github.com/hablamusic" rel="noopener"><strong>HablaMusic</strong><span>Родственный проект: бесплатные инструменты для ИИ-музыки и диджеев (промпты для Suno, BPM и тональность).</span></a></li>
</ul></section>
<footer class="foot"><div class="wrap foot-in">
<p><strong>UniqAI</strong> делает приложение для ИИ-фото, видео и чата: <a href="{home}" data-out="footer">uniqai.app</a>. Этот инструмент открыт под лицензией MIT, код на <a href="{repo}" rel="noopener">GitHub</a>.</p>
<p>{priv} Названия моделей принадлежат их владельцам, deslop-ru с ними не связан.</p>
<p>Автор: <a href="{rm}" rel="noopener">Vlad Yasinski</a> · <a href="{li}" rel="noopener">LinkedIn</a> · <a href="https://t.me/ua5er" rel="noopener">Telegram</a></p>
</div></footer>
<script>window.UQ={{key:"{ph}",repo:"{c}"}};</script>
{scripts}
</body></html>
""".format(browse=browse, tools=tools, home=esc(utm("/", content="footer")), repo=REPO, c=CAMPAIGN, li=LINKEDIN, rm=esc(ROIMOBI),
           ph=POSTHOG_KEY, scripts=scripts, priv=PRIVACY)


def breadcrumb(items):
    return {"@type": "BreadcrumbList", "@id": BASE + items[-1][1] + "#crumbs", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": BASE + p} for i, (n, p) in enumerate(items)]}


def org():
    return {"@type": "Organization", "@id": UNIQ + "/#org", "name": "UniqAI", "url": UNIQ + "/",
            "logo": {"@type": "ImageObject", "url": UNIQ + "/icon-512.png", "width": 512, "height": 512},
            "sameAs": ["https://github.com/uniqaiapp"]}


def website():
    return {"@type": "WebSite", "@id": HUB + "#site", "name": "Открытые инструменты UniqAI", "url": HUB}


def webapp():
    return {"@type": "WebApplication", "@id": BASE + "#app", "name": "deslop-ru: проверка текста на ИИ-штампы", "url": BASE,
            "applicationCategory": "UtilitiesApplication", "operatingSystem": "Any (web browser)",
            "description": "Проверка русского и английского текста на ИИ-штампы: оценка от 0 до 100, список найденных фраз с подсказками и безопасная вычистка.",
            "isAccessibleForFree": True, "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            "license": REPO + "/blob/main/LICENSE", "author": AUTHOR, "publisher": {"@id": UNIQ + "/#org"},
            "codeRepository": REPO, "image": OG_IMAGE, "sameAs": [REPO], "inLanguage": ["ru", "en"],
            "featureList": ["Оценка от 0 до 100", "%d шаблонов в %d категориях" % (N_PAT, N_CAT), "Безопасная вычистка", "Работает в браузере, текст не отправляется"]}


def page(path, title, desc, h1, lead, body, examples, crumbs, current="", kind="WebPage", extra_graph=None, buttons=None,
         builder=False, main_entity=None, compact=False):
    prefix = "../" * path.count("/")
    graph = [org(), website(),
             {"@type": kind, "@id": BASE + path + "#page", "url": BASE + path, "name": title, "description": desc,
              "inLanguage": "ru", "isPartOf": {"@id": HUB + "#site"}, "publisher": {"@id": UNIQ + "/#org"},
              "dateModified": SITE_UPDATED, "author": AUTHOR, "primaryImageOfPage": {"@type": "ImageObject", "url": OG_IMAGE}}]
    if main_entity:
        graph[2]["mainEntity"] = {"@id": main_entity}
    if len(crumbs) > 1:
        graph.append(breadcrumb(crumbs))
        graph[2]["breadcrumb"] = {"@id": BASE + path + "#crumbs"}
    graph += extra_graph or []
    crumb_html = ""
    if len(crumbs) > 1:
        crumb_html = '<nav class="crumbs" aria-label="Хлебные крошки">%s</nav>' % " / ".join(
            '<a href="%s%s">%s</a>' % (prefix, p, esc(n)) if i < len(crumbs) - 1 else '<span>%s</span>' % esc(n)
            for i, (n, p) in enumerate(crumbs))
    out = """<body>
<a class="skip" href="#main">К содержимому</a>
{header}
<main id="main">
<section class="hero{compact}"><div class="wrap hero-in">
{crumbs}
<p class="pill"><span class="dot"></span>бесплатно · открытый код · MIT</p>
<h1>{h1}</h1>
<p class="lead">{lead}</p>
<p class="byline">Обновлено {upd} · Автор: Vlad Yasinski (<a href="{li}" rel="noopener">LinkedIn</a>, <a href="{rm}" rel="noopener">roimobi.com</a>) · Код на <a href="{repo}" rel="noopener">GitHub</a></p>
<div class="hero-cta">{btns}</div>
</div></section>
{body}
</main>
""".format(header=header(prefix, current), crumbs=crumb_html, h1=esc(h1), lead=esc(lead), upd="26.11.2026",
           rm=esc(ROIMOBI), li=LINKEDIN, repo=REPO, btns="".join(buttons or []), body=body, compact=" hero-compact" if compact else "")
    return head(title, desc, path, graph, prefix) + out + footer(prefix, examples, builder)


def btn(href, label, ghost=False, out=None):
    return '<a class="btn%s" href="%s"%s>%s</a>' % (" btn-ghost" if ghost else "", esc(href), ' data-out="%s"' % out if out else "", esc(label))


def sec(title, inner, sid="", cls="ug-sec wrap"):
    return '<section class="%s"%s>\n<h2>%s</h2>\n%s\n</section>' % (cls, ' id="%s"' % sid if sid else "", esc(title), inner)


def answer_sec(question, answer, sid="answer"):
    return sec(question, '<p class="ug-answer">%s</p>' % esc(check_answer(answer, question)), sid)


def faq_html(items):
    return '<section class="faq wrap" aria-labelledby="faq-h"><h2 id="faq-h">Частые вопросы</h2>%s</section>' % "".join(
        "<details><summary>%s</summary><p>%s</p></details>" % (esc(q), esc(a)) for q, a in items)


def faq_graph(items):
    return {"@type": "FAQPage", "@id": BASE + "#faq", "mainEntity": [{"@type": "Question", "name": q,
                                                 "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items]}


def stack_table(headers, rows, cls="ug-table np-stack", row_ids=None):
    """rows are lists of ready-made HTML cells. On a phone each row becomes a block labelled by its column."""
    th = "".join('<th scope="col">%s</th>' % esc(h) for h in headers)
    trs = "".join("<tr%s>%s</tr>" % (' id="%s"' % row_ids[i] if row_ids else "",
                                      "".join('<td data-label="%s">%s</td>' % (esc(headers[j]), c) for j, c in enumerate(row)))
                  for i, row in enumerate(rows))
    return '<div class="ug-tablewrap"><table class="%s"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (cls, th, trs)


def author_block():
    return ('<section class="author wrap" aria-label="Об авторе"><p>Автор: <strong>Vlad Yasinski</strong>, AI growth consultant '
            '(<a href="%s" rel="noopener">roimobi.com</a>, <a href="%s" rel="noopener">LinkedIn</a>, <a href="https://github.com/ua5er" rel="noopener">GitHub</a>). '
            'Опубликовано вместе с UniqAI под лицензией MIT. %s</p></section>' % (esc(ROIMOBI), LINKEDIN, esc(PRIVACY)))


def ex_list(prefix, examples, exclude=None, limit=None, tryit=None):
    """tryit is the relative path to the checker page; when set each card gets a 'Проверить' link that loads the before text."""
    items = []
    for slug, b in examples.items():
        if slug == exclude:
            continue
        card = '<a href="{p}examples/{s}/"><strong>{t}</strong>{d}<em>{b} → {a}</em></a>'.format(
            p=prefix, s=slug, t=esc(b["chip"]), d=esc(b["card"]), b=b["rb"]["score"], a=b["ra"]["score"])
        if tryit is not None:
            items.append('<li class="np-try">%s<a class="np-tryit" href="%s?sample=%s#builder" aria-label="Загрузить исходный текст «%s» в проверку">Проверить</a></li>'
                         % (card, tryit, slug, esc(b["chip"])))
        else:
            items.append("<li>%s</li>" % card)
    if limit:
        items = items[:limit]
    return '<ul class="ug-list">%s</ul>' % "".join(items)


def code(s):
    return '<code class="dr-ph">%s</code>' % esc(s)


def pre_block(pid_, text, kind, label="Скопировать"):
    return ('<pre class="np-pre" id="%s">%s</pre><div class="ug-actions"><button type="button" class="btn btn-sm" data-copy="%s" data-kind="%s" data-label="%s">%s</button></div>'
            % (pid_, esc(text), pid_, kind, label, label))


# ---------------------------------------------------------------- pages

def home_page(examples):
    form = """<div class="ug-form" id="ug-form">
<label class="ug-f" for="dr-text"><span>Ваш текст</span></label>
<textarea id="dr-text" rows="9" spellcheck="false" autocomplete="off" aria-describedby="dr-count" placeholder="Вставьте сюда текст на русском или английском"></textarea>
<p class="np-meta"><span id="dr-count">0 слов</span></p>
<fieldset><legend>Или загрузите пример</legend><div class="np-samples">{samples}</div></fieldset>
<div class="ug-btns"><button type="button" class="btn" id="dr-run">Проверить</button><button type="button" class="btn btn-ghost" id="dr-clear">Очистить</button></div>
<p class="ug-status" id="dr-status" aria-live="polite"></p>
<p class="np-priv">{priv}</p>
<noscript><p class="ug-small">Проверке на странице нужен JavaScript. То же самое делает скрипт из репозитория: <code>python3 scripts/deslop.py check файл.md</code>.</p></noscript>
</div>""".format(priv=esc(PRIVACY), samples="".join(
        '<button type="button" data-sample="%s" aria-pressed="false">%s</button>' % (s, esc(b["chip"])) for s, b in examples.items()))
    builder = """<section class="ug-builder wrap" id="builder" aria-labelledby="builder-h">
<h2 id="builder-h">Проверьте свой текст</h2>
<div class="ug-bar ug-bar-empty" id="ug-bar" aria-live="polite"><span>{bar}</span><a href="#ug-out">Смотреть результат</a></div>
<div class="ug-layout">
{form}
<div class="ug-out" id="ug-out" aria-live="polite">
<div id="ug-lint"><p class="ug-small">{empty}</p></div>
</div>
</div>
<script type="application/json" id="ug-data">{data}</script>
</section>""".format(bar=esc(UI["emptyBar"]), form=form, empty=esc(UI["empty"]), data=jdump(data_json(examples)))
    cats = '<ul class="ug-list">%s</ul>' % "".join(
        '<li><a href="patterns/#cat-{k}"><strong>{n}</strong>{d}<em>{c}</em></a></li>'.format(
            k=k, n=esc(v[0]), d=esc(v[2]), c=("%d %s" % (sum(1 for p in D.PATTERNS if p["category"] == k), ru_plural(sum(1 for p in D.PATTERNS if p["category"] == k), ["шаблон", "шаблона", "шаблонов"]))
                                              if k != "structure" else "%d проверок формы" % len(STRUCT)))
        for k, v in D.CATEGORIES.items())
    bands = stack_table(["Оценка", "Вердикт", "Что делать"], [
        ["<b>0 до 9</b>", "чисто", "Ничего. Но это не доказывает, что писал человек."],
        ["<b>10 до 29</b>", "лёгкий налёт", "Уберите отмеченные фразы, остальное можно оставить."],
        ["<b>30 до 59</b>", "заметно", "Перепишите отмеченные места, читатель их увидит."],
        ["<b>60 до 100</b>", "читается как бот", "Перепишите текст целиком, подсказки в категориях помогут."]])
    english = ('<div class="dr-en" lang="en"><p><b>In English.</b> deslop-ru finds the phrases that make Russian and English text read as machine-written: empty openers, '
               'bureaucratic wording, English calques, hype adjectives, triplets, chat residue. It scores a text from 0 to 100, lists every hit with a fix and can cut %d safe filler phrases.</p>'
               '<p>The checker runs in your browser and your text is never uploaded. It is also a Claude Code skill, a Cursor rule and a plain Python script. MIT licensed. '
               '<a href="%s" rel="noopener">Source on GitHub</a>.</p></div>' % (N_CUT, REPO))
    second = ('<p class="ug-small">Чекер ищет приёмы, а не авторство. Если нужна вероятностная оценка, у UniqAI есть детектор ИИ-текста: проверка стоит 8 гемов, '
              'надёжнее всего он работает с английским, а результат это вероятность, а не доказательство.</p>'
              '<div class="ug-cta"><p>Нужно второе мнение о тексте?</p><a class="btn btn-sm" href="%s" data-out="home-detector">Открыть детектор ИИ-текста</a></div>'
              % esc(utm("/detect/ai-text-detector", content="home")))
    body = "\n".join([
        builder,
        answer_sec("Как убрать ИИ-штампы из текста?", HOME_ANSWER),
        sec("Что ищет проверка", cats, "categories"),
        sec("Как читать оценку", bands + '<p class="ug-small">Сумма весов находок делится на число слов, умножается на 100 и на 8. Это подсказка для чтения, а не приговор тексту.</p>', "score"),
        sec("Шесть примеров, до и после", ex_list("", examples, tryit="") + '<p class="ug-small">Откройте пару, чтобы увидеть, что изменилось и почему. Обе оценки посчитал тот же чекер.</p>', "examples"),
        sec("Второе мнение", second, "second"),
        sec("In English", english, "english"),
        faq_html(FAQ),
        author_block(),
    ])
    return page("", fit(["Убрать ИИ-штампы из текста онлайн" + SUFFIX], 1, 60, "title"),
                fit_desc(["Бесплатная проверка русского текста на ИИ-штампы: оценка от 0 до 100, номера строк и подсказки. Работает в браузере, текст не уходит.",
                          "Проверка русского текста на ИИ-штампы: оценка от 0 до 100, найденные фразы и подсказки. Бесплатно, работает в браузере."]),
                "Убрать ИИ-штампы из текста: бесплатная проверка русского текста онлайн",
                "Вставьте текст и получите оценку от 0 до 100, найденные штампы с подсказками и вычищенную версию. Всё считается в браузере.",
                body, examples, [("Проверка", "")], current="", kind="WebPage", builder=True, compact=True,
                extra_graph=[webapp(), faq_graph(FAQ)], main_entity=BASE + "#app",
                buttons=[btn("#builder", "Проверить текст"), btn("examples/", "Смотреть примеры", ghost=True)])


def examples_page(examples):
    rows = [['<a href="%s/">%s</a>' % (s, esc(b["chip"])), "%d (%s)" % (b["rb"]["score"], b["rb"]["verdict"]), "%d (%s)" % (b["ra"]["score"], b["ra"]["verdict"])]
            for s, b in examples.items()]
    body = "\n".join([
        answer_sec("Как выглядит текст без ИИ-штампов?", EXAMPLES_ANSWER),
        sec("Все шесть примеров", ex_list("../", examples, tryit="../") + '<p class="ug-small">На карточке сначала оценка оригинала, потом правки. Откройте пару, чтобы скопировать правку, или нажмите «Проверить», чтобы загрузить оригинал в чекер.</p>', "list"),
        sec("Как читать оценки", '<p class="ug-small">Оценка показывает, сколько в тексте типовых приёмов, а не качество мысли. Нулевая правка не гарантирует хороший текст: без фактов она тоже будет пустой.</p>'
            '<details class="why"><summary>Оценки таблицей и как их воспроизвести</summary>' + stack_table(["Пример", "До", "После"], rows)
            + '<p class="ug-small">Для разработчиков: команда <code>python3 scripts/deslop.py check examples/*.md</code> из корня репозитория печатает все строки.</p></details>', "scores"),
        author_block(),
    ])
    lo = min(b["rb"]["score"] for b in examples.values())
    return page("examples/", fit(["Примеры текстов без ИИ-штампов, до и после" + SUFFIX], 1, 60, "title"),
                fit_desc(["Шесть пар до и после: статья, ответ чат-бота, рассылка, карточка товара, заметки о релизе и пост. Оценка до: от %d до 100, после: 0." % lo]),
                "Примеры текстов без ИИ-штампов, до и после",
                "Шесть жанров: что выдаёт нейросеть, что остаётся после правки и почему. Оценки считает настоящий чекер.",
                body, examples, [("Проверка", ""), ("Примеры", "examples/")], current="examples/", kind="CollectionPage",
                buttons=[btn("../#builder", "Проверить свой текст")])


def example_body(slug, b, examples):
    rb, ra = b["rb"], b["ra"]
    answer = "%s Чекер ставит оригиналу %d из 100, правке %d из 100." % (b["gist"], rb["score"], ra["score"])
    meta = ('<p class="np-ex-meta"><span>До <b>%d/100</b> (%s)</span><span>После <b>%d/100</b> (%s)</span><span>%d %s → %d %s</span></p>'
            % (rb["score"], esc(rb["verdict"]), ra["score"], esc(ra["verdict"]), rb["words"], ru_plural(rb["words"], ["слово", "слова", "слов"]),
               ra["words"], ru_plural(ra["words"], ["слово", "слова", "слов"])))
    pair = ('<div class="ug-pair"><div class="ug-fail"><p><b>До</b> · %d/100</p><pre>%s</pre></div>'
            '<div class="ug-pass"><p><b>После</b> · %d/100</p><pre id="dr-after">%s</pre>'
            '<div class="ug-actions"><button type="button" class="btn btn-sm" data-copy="dr-after" data-kind="after" data-label="Скопировать правку">Скопировать правку</button></div></div></div>'
            % (rb["score"], esc(b["before"]), ra["score"], esc(b["after"])))
    actions = '<p class="np-ex-actions">%s</p>' % btn("../../?sample=" + slug + "#builder", "Проверить исходный текст самому", ghost=True)
    rows = []
    for c in D.CATEGORIES:
        n = rb["by_category"].get(c, 0)
        if not n:
            continue
        ph = phrases_of(rb, c)
        cell = ", ".join("<mark>«%s»</mark>" % esc(x) for x in ph) if c != "structure" else ", ".join(esc(x) for x in ph)
        rows.append([esc(D.CATEGORIES[c][0]), str(n), cell, "%d" % ra["by_category"].get(c, 0)])
    table = stack_table(["Категория", "Было", "Примеры", "Стало"], rows) if rows else '<p class="ug-small">В оригинале нет заметных штампов.</p>'
    report = ('<details class="why"><summary>Отчёт командной строки для оригинала</summary><pre class="np-pre">%s</pre></details>' % esc(b["report"].rstrip("\n")))
    cta = ('<div class="ug-cta"><p>Хотите переписать свой текст по тем же правилам? В чате UniqAI доступны модели OpenAI, Google, DeepSeek, Anthropic и xAI.</p>'
           '<a class="btn btn-sm" href="%s" data-out="example">Открыть чат UniqAI</a></div>' % esc(utm("/chat", content="example")))
    others = [(s, o) for s, o in examples.items() if s != slug]
    rel = {s: o for s, o in others[:3]}
    parts = [
        answer_sec(b["q"], answer),
        sec("Текст до и после", meta + pair + actions, "prompts"),
        sec("Что изменилось", table + '<p class="ug-small">Отмечены фразы, которые нашёл чекер в оригинале. После правки в тех же категориях осталось столько, сколько показано в последней колонке.</p>', "added"),
        sec("Почему правка работает", '<p class="ug-answer-plain">%s</p>%s%s' % (esc(b["why"]), cta, report), "why"),
        sec("Другие примеры", ex_list("../../", rel), "more"),
        author_block(),
    ]
    return "\n".join(parts), answer


def example_pages(examples):
    pages = {}
    for slug, b in examples.items():
        rb, ra = b["rb"], b["ra"]
        body, _ = example_body(slug, b, examples)
        title = fit_title(b["core"])
        desc = fit_desc(["До и после: %s. Оригинал получает %d из 100, правка %d из 100. Можно скопировать текст и проверить свой." % (b["short"], rb["score"], ra["score"]),
                         "До и после: %s. Оценка оригинала %d из 100, правки %d из 100. Копируйте правку и проверяйте свой текст." % (b["short"], rb["score"], ra["score"]),
                         "%s: оригинал %d из 100, правка %d из 100. Копируйте правку и проверяйте свой текст." % (b["short"].capitalize(), rb["score"], ra["score"])])
        path = "examples/%s/" % slug
        pages[path] = page(path, title, desc, b["h1"],
                           "Текст, каким его пишет нейросеть, правка и объяснение, что изменилось. Обе оценки посчитал настоящий чекер.",
                           body, examples, [("Проверка", ""), ("Примеры", "examples/"), (b["chip"], path)], current="examples/",
                           buttons=[btn("../../?sample=" + slug + "#builder", "Проверить исходный текст"), btn("../", "Все примеры", ghost=True)])
    return pages


def patterns_page(examples):
    body = [answer_sec("Какие ИИ-штампы ищет чекер?", PATTERNS_ANSWER)]
    jump = '<p class="np-jump">%s</p>' % " ".join('<a href="#cat-%s">%s</a>' % (k, esc(v[0])) for k, v in D.CATEGORIES.items())
    body.append(sec("Категории", '<p class="ug-small">Вес показывает, насколько сильно фраза выдаёт генерацию: 1 слабо, 3 сильно. Значок «вычистка» значит, что режим strip удаляет фразу без потери смысла.</p>' + jump, "use"))
    for k, v in D.CATEGORIES.items():
        pats = [p for p in D.PATTERNS if p["category"] == k]
        if k == "structure":
            rows = [[code(label), esc(rule), str(w), "нет"] for _, label, rule, w in STRUCT]
            ids = ["p-" + pid(i) for i, *_ in STRUCT]
            inner = '<p class="ug-small">%s</p>' % esc(v[2]) + stack_table(["Проверка", "Когда срабатывает", "Вес", "Вычистка"], rows, cls="ug-table np-stack dr-tbl", row_ids=ids)
        else:
            rows = [['<a class="dr-anchor" href="#p-%s" aria-label="Ссылка на шаблон">#</a>%s' % (pid(p["id"]), code(p["label"])), esc(p["fix"]),
                     str(p["weight"]), "да" if p["cut"] else "нет", '<span class="dr-lang">%s</span>' % p["lang"]] for p in pats]
            ids = ["p-" + pid(p["id"]) for p in pats]
            inner = '<p class="ug-small">%s</p>' % esc(v[2]) + stack_table(["Шаблон", "Что делать", "Вес", "Вычистка", "Язык"], rows, cls="ug-table np-stack dr-tbl", row_ids=ids)
        body.append(sec("%s (%d)" % (v[0], len(pats) if k != "structure" else len(STRUCT)), inner, "cat-" + k))
    body.append(sec("Проверить текст по этому каталогу", '<p class="ug-small">Чекер на главной странице применяет все эти шаблоны и показывает, какие сработали.</p>'
                    '<p class="np-ex-actions">%s</p>' % btn("../#builder", "Открыть проверку", ghost=True), "check"))
    body.append(author_block())
    return page("patterns/", fit(["Каталог ИИ-штампов в русском тексте" + SUFFIX], 1, 60, "title"),
                fit_desc(["Каталог из %d шаблонов, по которым русский и английский текст выдаёт нейросеть: вес, подсказка и пометка о безопасной вычистке." % N_PAT,
                          "Каталог из %d шаблонов ИИ-штампов: пустые зачины, канцелярит, кальки, тройки, следы чата. У каждого вес и подсказка." % N_PAT]),
                "Каталог ИИ-штампов: что выдаёт нейросеть в русском тексте",
                "Все %d шаблонов и 7 проверок формы с весом и подсказкой, чем заменить. У каждого есть своя ссылка." % N_PAT,
                "\n".join(body), examples, [("Проверка", ""), ("Шаблоны", "patterns/")], current="patterns/", kind="CollectionPage",
                buttons=[btn("../#builder", "Проверить текст")])


def howto_page(examples):
    body = [answer_sec("Как установить deslop-ru?", HOWTO_ANSWER)]
    cc = ('<p class="ug-small">Скилл ставится в папку скиллов. Для всех проектов:</p>'
          + pre_block("dr-i1", "git clone https://github.com/uniqaiapp/deslop-ru ~/.claude/skills/deslop-ru", "install")
          + '<p class="ug-small">Только для одного проекта:</p>'
          + pre_block("dr-i2", "git clone https://github.com/uniqaiapp/deslop-ru .claude/skills/deslop-ru", "install")
          + '<p class="ug-small">Или через каталог скиллов:</p>'
          + pre_block("dr-i3", "npx skills add uniqaiapp/deslop-ru", "install")
          + '<p class="ug-small">Через плагин: сначала добавьте каталог, потом поставьте скилл.</p>'
          + pre_block("dr-i4", "/plugin marketplace add uniqaiapp/skills\n/plugin install deslop-ru@uniqaiapp", "install")
          + '<p class="ug-small">Дальше напишите <code>/deslop-ru</code> или попросите: «убрать ИИ-штампы из этого файла».</p>')
    cur = ('<p class="ug-small">Скопируйте <a href="%s/blob/main/.cursor/rules/deslop-ru.mdc" rel="noopener">.cursor/rules/deslop-ru.mdc</a> в папку <code>.cursor/rules/</code> проекта '
           'вместе с <code>SKILL.md</code>, <code>scripts/</code> и <code>references/</code>. Правило подключает скилл через <code>@SKILL.md</code>.</p>' % REPO)
    cod = ('<p class="ug-small">Скопируйте <code>SKILL.md</code>, <code>scripts/</code> и <code>references/</code> в <code>.agents/skills/deslop-ru/</code> '
           'и добавьте блок из <a href="%s/blob/main/codex/INSTRUCTIONS.md" rel="noopener">codex/INSTRUCTIONS.md</a> в свой <code>AGENTS.md</code>. '
           'Блок просит агента запускать проверку до и после правки и сообщать оценку:</p>' % REPO
           + pre_block("dr-i5", "python3 .agents/skills/deslop-ru/scripts/deslop.py check <файл>", "install"))
    cli = ('<p class="ug-small">Скрипту нужен только Python 3.9 и новее. Четыре команды:</p>'
           + pre_block("dr-i6", "python3 scripts/deslop.py check текст.md    # находки с номерами строк и оценка\n"
                                "python3 scripts/deslop.py audit текст.md    # разбор по категориям и метрики формы\n"
                                "python3 scripts/deslop.py strip текст.md    # безопасная вычистка, печатает результат\n"
                                "python3 scripts/deslop.py stats             # сколько шаблонов в каждой категории", "install")
           + '<p class="ug-small">В CI поставьте порог по оценке: сборка упадёт, если текст набрал больше 20.</p>'
           + pre_block("dr-i7", "python3 scripts/deslop.py check --fail-over 20 docs/*.md", "install"))
    body += [sec("Claude Code", cc, "claude-code"), sec("Cursor", cur, "cursor"), sec("Codex и другие агенты с AGENTS.md", cod, "codex"),
             sec("Без агента: командная строка и CI", cli, "cli"),
             sec("Сначала проверьте в браузере", '<p class="ug-small">Не хотите ничего ставить? Та же проверка работает на главной странице без установки.</p>'
                 '<p class="np-ex-actions">%s</p>' % btn("../#builder", "Проверить текст онлайн", ghost=True), "try"),
             author_block()]
    return page("how-to/", fit(["Установка скилла deslop-ru: Claude, Cursor, Codex" + SUFFIX, "Установка deslop-ru для Claude, Cursor, Codex" + SUFFIX], 1, 60, "title"),
                fit_desc(["Как поставить deslop-ru в Claude Code, Cursor и Codex и как запускать чекер из командной строки и CI. Нужен только Python 3.9 и новее.",
                          "Как поставить deslop-ru в Claude Code, Cursor и Codex и запускать чекер в терминале и CI. Нужен только Python."]),
                "Как поставить deslop-ru в Claude Code, Cursor и Codex",
                "Три способа подключить скилл и четыре команды чекера. Зависимостей нет, нужен только Python.",
                "\n".join(body), examples, [("Проверка", ""), ("Установка", "how-to/")], current="how-to/",
                buttons=[btn("../#builder", "Проверить текст")])


# ---------------------------------------------------------------- site files

def not_found():
    return """<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Страница не найдена | deslop-ru</title><meta name="robots" content="noindex"><link rel="icon" href="/deslop-ru/assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/deslop-ru/site.css"></head>
<body><main class="wrap" style="padding:20vh 24px 10vh"><h1>Страница не найдена</h1><p class="lead">Такой страницы нет. Проверка текста здесь: <a href="/deslop-ru/">deslop-ru</a>.</p>
<p class="byline">Или откройте: <a href="/deslop-ru/examples/">примеры до и после</a> · <a href="/deslop-ru/patterns/">каталог шаблонов</a> · <a href="/deslop-ru/how-to/">установка</a> · <a href="https://uniqaiapp.github.io/">все открытые инструменты UniqAI</a></p></main></body></html>
"""


def llms_txt(examples):
    lines = ["# deslop-ru: убрать ИИ-штампы из русского текста (UniqAI, open source)", "",
             "> Бесплатная проверка текста в браузере: оценка от 0 до 100, список найденных штампов с номерами строк и подсказками, безопасная вычистка. "
             "%d шаблонов (%d русских, %d английских) в %d категориях и 7 проверок формы. Текст не покидает браузер. Код под MIT. Автор: Vlad Yasinski (%s)." % (N_PAT, N_RU, N_EN, N_CAT, LINKEDIN),
             "", "> English: deslop-ru finds the phrases that make Russian and English text read as machine-written, scores a text from 0 to 100, lists every hit with a fix and "
             "cuts %d safe filler phrases. It runs in the browser, nothing is uploaded. Also a Claude Code skill, a Cursor rule and a stdlib Python script. MIT." % N_CUT,
             "", "## Страницы / Pages", "",
             "- [Проверка текста](%s): вставьте текст, получите оценку, находки и вычищенную версию (text checker)" % BASE,
             "- [Примеры](%sexamples/): %d пар до и после (before and after examples)" % (BASE, len(examples)),
             "- [Каталог шаблонов](%spatterns/): %d шаблонов и 7 проверок формы, у каждого своя ссылка (pattern catalogue)" % (BASE, N_PAT),
             "- [Установка](%show-to/): Claude Code, Cursor, Codex, командная строка и CI (install)" % (BASE),
             "", "## Примеры / Examples", ""]
    for slug, b in examples.items():
        lines.append("- [%s](%sexamples/%s/): оценка %d, после правки %d" % (b["chip"], BASE, slug, b["rb"]["score"], b["ra"]["score"]))
    lines += ["", "## Заметки / Notes", "",
              "- Оценка строится на правилах (шаблоны и проверки формы, без нейросети). Она показывает приёмы, а не авторство: ноль не доказывает, что писал человек.",
              "- The score is rule-based, not a detector of machine authorship.",
              "- Текст остаётся в браузере; считаются только анонимные просмотры, клики и уровень результата.",
              "", "## Источник / Source", "", "- [Репозиторий](%s): scripts/deslop.py (CLI без зависимостей), SKILL.md, примеры и справочники" % REPO,
              "", "## Дальше / Next", "",
              "- [UniqAI чат](%s): переписать текст в чате с моделями OpenAI, Google, DeepSeek, Anthropic и xAI" % utm("/chat", medium="llms"), ""]
    return "\n".join(lines)


def sitemap(paths):
    urls = "".join("<url><loc>%s%s</loc><lastmod>%s</lastmod></url>" % (BASE, p, SITE_UPDATED) for p in paths)
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>\n' % urls


def build_pages(examples):
    pages = {"": home_page(examples), "examples/": examples_page(examples)}
    pages.update(example_pages(examples))
    pages["patterns/"] = patterns_page(examples)
    pages["how-to/"] = howto_page(examples)
    return pages


def render_all():
    examples = load_examples()
    pages = build_pages(examples)
    files = {p + "index.html": c for p, c in pages.items()}
    files["404.html"] = not_found()
    files["llms.txt"] = llms_txt(examples)
    files["sitemap.xml"] = sitemap(list(pages))
    files["robots.txt"] = "User-agent: *\nAllow: /\n\nSitemap: %ssitemap.xml\n" % BASE
    files[".nojekyll"] = ""
    files[INDEXNOW_KEY + ".txt"] = INDEXNOW_KEY
    return files


def write_tree(out):
    for rel, content in render_all().items():
        dst = os.path.join(out, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
    for dirpath, _, names in os.walk(STATIC):
        for n in names:
            src = os.path.join(dirpath, n)
            dst = os.path.join(out, os.path.relpath(src, STATIC))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
    for asset in ("social-preview.png", "banner-dark.jpg", "banner-light.jpg"):
        src = os.path.join(ROOT, "assets", asset)
        if os.path.exists(src):
            dst = os.path.join(out, "assets", asset)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)


def tree(root):
    out = {}
    for dirpath, _, names in os.walk(root):
        for n in names:
            p = os.path.join(dirpath, n)
            with open(p, "rb") as f:
                out[os.path.relpath(p, root)] = f.read()
    return out


def main():
    tmp = tempfile.mkdtemp(prefix="dr-site-")
    try:
        write_tree(tmp)
        new = tree(tmp)
        if "--check" in sys.argv:
            old = tree(OUT) if os.path.isdir(OUT) else {}
            stale = sorted(k for k in set(new) | set(old) if new.get(k) != old.get(k))
            if stale:
                print("docs/ is out of date, run: python3 scripts/site.py\n  " + "\n  ".join(stale))
                return 1
            print("docs/ up to date (%d files)" % len(new))
            return 0
        if os.path.isdir(OUT):
            shutil.rmtree(OUT)
        shutil.copytree(tmp, OUT)
        print("wrote %d files to docs/" % len(new))
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
