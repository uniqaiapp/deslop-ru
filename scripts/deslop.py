#!/usr/bin/env python3
"""deslop.py: flag AI-writing patterns ("ИИ-штампы") in Russian or English text.

Zero dependencies, Python 3.9+. Four modes:

  check    list every hit with line number, category and a fix hint; print the score
  audit    category breakdown, structure checks, density and a verdict
  strip    remove only the phrases that can be cut without changing meaning
  stats    count patterns per language and category (the README numbers come from here)
  patterns dump the pattern table as Markdown (references/patterns.md is generated from it)

Score: 8 x weighted hits per 100 words, capped at 100. It is a heuristic, not a detector.
Author: UniqAI <support@uniqai.app>. License: MIT.
"""
import argparse
import json
import re
import sys
import unicodedata

VERSION = "0.1.0"

# ---------------------------------------------------------------------------
# Pattern table
# ---------------------------------------------------------------------------
# Each pattern: id, lang, category, regex (applied to a lowercased copy with ё->е),
# label (what the reader sees), fix (what to do instead), weight (1 light, 2 typical, 3 strong tell),
# cut (True when `strip` may delete the phrase outright; the regex then includes its trailing punctuation).
#
# Russian regexes are written with "е" only; the matcher folds ё to е before matching.
# Word boundaries: Python's \b works for Cyrillic letters in str patterns.

CATEGORIES = {
    "intro": ("Пустые зачины", "Empty openers",
              "Фразы, которые занимают первое предложение и ничего не сообщают."),
    "filler": ("Пустые вводные", "Empty connectives",
               "Вводные обороты, которые обещают важность вместо того, чтобы её показать."),
    "bureau": ("Канцелярит", "Bureaucratic register",
               "Отглагольные существительные, «данный», «осуществлять», «в рамках»: язык справки, а не человека."),
    "calque": ("Кальки с английского", "English calques",
               "Обороты, перенесённые из английского маркетинга: «погрузимся», «на новый уровень», «это не просто X, это Y»."),
    "hype": ("Оценочные штампы", "Hype adjectives",
             "«Уникальный», «инновационный», «мощный инструмент»: оценка вместо факта."),
    "triplet": ("Тройки", "Triplets",
                "Три прилагательных или существительных через запятую и «и»: ритм нейросети."),
    "outro": ("Пустые выводы", "Empty conclusions",
              "«Подводя итог», «надеюсь, было полезно»: абзац, который повторяет текст или ничего не добавляет."),
    "chat": ("Следы чата", "Chat residue",
             "Фразы ассистента, которые остались в тексте: «Конечно!», «Вот несколько», «Надеюсь, это поможет»."),
    "rhetoric": ("Риторика", "Rhetorical tics",
                 "Риторические вопросы, «спойлер», «и вот почему»: приёмы, которые нейросеть ставит через абзац."),
    "structure": ("Структура", "Structure",
                  "Не фразы, а форма: эмодзи-маркеры, простыни списков, тире через слово, жирный заголовок в каждом пункте."),
}

# (id, lang, category, regex, label, fix, weight, cut)
_P = [
    # ---- intro ---------------------------------------------------------------
    ("ru.intro.modern_world", "ru", "intro",
     r"в (современном|нашем|сегодняшнем|нынешнем) (быстро меняющемся |динамичном |цифровом )?(мире|обществе)(,\s*(где|когда|в котором|который|которая|которое)[^,\n]*)?[,:]?[ \t]*",
     "в современном мире", "Уберите. Начните с факта или с того, что изменилось.", 3, True),
    ("ru.intro.nashe_vremya", "ru", "intro",
     r"\bв (наше|нынешнее|настоящее) время[,:]?[ \t]*",
     "в наше время", "Уберите или назовите год, событие, причину.", 2, True),
    ("ru.intro.epoch", "ru", "intro",
     r"\bв (эпоху|век|эру) (цифровых технологий|цифровизации|искусственного интеллекта|ии|нейросетей|информации)(,\s*(где|когда|в котор(ой|ом|ую)|котор(ый|ая|ое))[^,\n]*)?[,:]?[ \t]*",
     "в эпоху цифровых технологий", "Уберите. Читатель знает, какой сейчас век.", 3, True),
    ("ru.intro.lets_figure", "ru", "intro",
     r"\bдавайте (же )?(разберемся|разбираться|рассмотрим|поговорим|выясним|посмотрим|обсудим)[^.!?\n]*[.!?:]?[ \t]*",
     "давайте разберёмся", "Уберите приглашение и сразу разбирайтесь.", 3, True),
    ("ru.intro.in_this_article", "ru", "intro",
     r"\bв (этой|данной|нашей) (статье|заметке|публикации|посте|материале) (мы|вы|я)\b",
     "в этой статье мы", "Уберите. Первое предложение должно быть самым полезным.", 2, False),
    ("ru.intro.today_we", "ru", "intro",
     r"\bсегодня (мы|я) (поговорим|расскажем|расскажу|разберем|разберу|рассмотрим|обсудим)\b",
     "сегодня мы поговорим", "Уберите анонс, оставьте содержание.", 2, False),
    ("ru.intro.no_secret", "ru", "intro",
     r"\b(ни для кого )?не секрет, что[ \t]*", "не секрет, что",
     "Уберите. Если не секрет, зачем говорить.", 3, True),
    ("ru.intro.as_known", "ru", "intro",
     r"\b(как (всем )?известно|все (мы )?знаем, что|всем известно, что)[,]?[ \t]*",
     "как известно", "Уберите или дайте источник.", 2, True),
    ("ru.intro.imagine", "ru", "intro",
     r"\bпредставьте( себе)?[,:]?[ \t]*", "представьте себе",
     "Уберите; опишите сцену напрямую.", 1, True),
    ("ru.intro.nowadays", "ru", "intro",
     r"\b(на сегодняшний день|в настоящее время|на данный момент)[,]?[ \t]*",
     "на сегодняшний день", "«Сейчас» или ничего.", 2, True),

    # ---- filler ---------------------------------------------------------------
    ("ru.filler.important_to_note", "ru", "filler",
     r"\b(важно|стоит|следует|нужно|необходимо|нельзя не|хочется|хотелось бы) (также |еще раз |особо )?(отметить|подчеркнуть|упомянуть|заметить|понимать|помнить|учитывать|сказать|добавить)(, что)?[ \t]*",
     "важно отметить", "Уберите оборот, оставьте то, что отмечали.", 3, True),
    ("ru.filler.obviously", "ru", "filler",
     r"\b(безусловно|несомненно|однозначно|бесспорно|очевидно|разумеется|конечно же)[,][ \t]*",
     "безусловно,", "Уберите. Если это очевидно, не говорите; если нет, докажите.", 2, True),
    ("ru.filler.thus", "ru", "filler",
     r"\b(таким образом|итак|в целом|в конечном (итоге|счете)|в общем и целом|так или иначе)[,][ \t]*",
     "таким образом,", "Уберите связку; предложения и так стоят рядом.", 2, True),
    ("ru.filler.worth_saying", "ru", "filler",
     r"\b(стоит|надо|нужно) (сказать|признать|заметить), что[ \t]*",
     "стоит сказать, что", "Уберите и скажите.", 2, True),
    ("ru.filler.also", "ru", "filler",
     r"\b(кроме того|помимо этого|более того|к тому же|также стоит|при этом важно)[,][ \t]*",
     "кроме того,", "Чаще всего можно убрать; абзац не развалится.", 1, True),
    ("ru.filler.in_general", "ru", "filler",
     r"\b(в принципе|по сути|по большому счету|в общем-то)[,][ \t]*",
     "по сути,", "Уберите.", 1, True),
    ("ru.filler.it_is_true", "ru", "filler",
     r"\b(действительно|на самом деле|по-настоящему|поистине|воистину)\b",
     "действительно", "Уберите усилитель; факт сильнее без него.", 1, False),

    # ---- bureau ----------------------------------------------------------------
    ("ru.bureau.dannyj", "ru", "bureau",
     r"\bданн(ый|ая|ое|ого|ой|ому|ую)\b(?! (момент|вопрос)е?\b)",
     "данный", "«Этот» или ничего. (Формы множественного числа не считаются: «по данным» — это про данные.)", 2, False),
    ("ru.bureau.osushchestvlyat", "ru", "bureau",
     r"\bосуществл(ять|яет|яют|яем|яете|яешь|яю|ение|ения|ении|яется|яются|ял|яла|яли)\b",
     "осуществлять", "Замените глаголом действия: «делать», «проводить», «запускать».", 2, False),
    ("ru.bureau.yavlyaetsya", "ru", "bureau",
     r"\bявля(ется|ются|лся|лась|лись)\b",
     "является", "Уберите связку: «X является Y» → «X — Y» или просто «X Y».", 1, False),
    ("ru.bureau.v_ramkah", "ru", "bureau",
     r"\bв рамках\b", "в рамках", "«В», «на», «во время» или перестройте фразу.", 2, False),
    ("ru.bureau.s_celyu", "ru", "bureau",
     r"\b(с целью|в целях)\b", "с целью", "«Чтобы».", 2, False),
    ("ru.bureau.v_svyazi", "ru", "bureau",
     r"\bв связи с (этим|чем|тем, что)\b", "в связи с этим", "«Поэтому».", 2, False),
    ("ru.bureau.predstavlyaet_soboj", "ru", "bureau",
     r"\bпредставля(ет|ют) собой\b", "представляет собой", "«Это» или тире.", 2, False),
    ("ru.bureau.imeet_mesto", "ru", "bureau",
     r"\bиме(ет|ют|ло|ли) место\b", "имеет место", "«Есть», «бывает», «случается».", 2, False),
    ("ru.bureau.okazyvaet", "ru", "bureau",
     r"\bоказыва(ет|ют|ть|ла|ло|ли) (влияние|воздействие|поддержку|помощь|содействие)\b",
     "оказывает влияние", "«Влияет», «помогает».", 2, False),
    ("ru.bureau.proizvodit", "ru", "bureau",
     r"\bпроизв(одить|одит|одят|ести|ел|ела|ели) (оценку|проверку|анализ|расчет|замер|настройку|установку)\b",
     "производить оценку", "«Оценить», «проверить», «посчитать».", 2, False),
    ("ru.bureau.v_processe", "ru", "bureau",
     r"\bв процессе (работы|использования|эксплуатации|обучения|реализации|внедрения)\b",
     "в процессе работы", "«Во время», «когда» или уберите.", 1, False),
    ("ru.bureau.putem", "ru", "bureau",
     r"\b(путем|посредством|при помощи|с помощью использования)\b",
     "путём / посредством", "«Через», «с помощью» или творительный падеж.", 1, False),
    ("ru.bureau.obespechivat", "ru", "bureau",
     r"\bобеспечива(ет|ют|ть|ется|ются)\b", "обеспечивать",
     "Назовите действие: «даёт», «держит», «защищает».", 1, False),
    ("ru.bureau.funkcional", "ru", "bureau",
     r"\bфункционал(а|у|ом|е)?\b", "функционал", "«Функции», «возможности».", 1, False),
    ("ru.bureau.nalichie", "ru", "bureau",
     r"\b(при наличии|в случае отсутствия|наличие|отсутствие) (возможности|необходимости|желания)\b",
     "при наличии возможности", "«Если можно», «если нужно», «если хочется».", 2, False),
    ("ru.bureau.v_sluchae_esli", "ru", "bureau",
     r"\bв случае,? если\b", "в случае если", "«Если».", 2, False),
    ("ru.bureau.aktualnyj", "ru", "bureau",
     r"\bактуальн(ый|ая|ое|ые|ость|ости|ым|ых|ую)\b", "актуальный",
     "Скажите, для кого и почему сейчас; иначе уберите.", 1, False),

    # ---- calque ----------------------------------------------------------------
    ("ru.calque.dive_in", "ru", "calque",
     r"\b(давайте )?(погруз(имся|иться|имся глубже)|нырнем|окунемся)\b",
     "погрузимся (let's dive in)", "Уберите; начинайте с темы.", 3, False),
    ("ru.calque.next_level", "ru", "calque",
     r"\bна (новый|следующий|качественно новый|принципиально новый) уровень\b",
     "на новый уровень (next level)", "Скажите, что конкретно станет лучше и насколько.", 3, False),
    ("ru.calque.unlock_potential", "ru", "calque",
     r"\b(раскр(ыть|ывает|оет|ойте)|реализ(овать|ует)) (свой |весь |полный |ваш |скрытый )?потенциал\b",
     "раскрыть потенциал (unlock potential)", "Назовите результат.", 3, False),
    ("ru.calque.game_changer", "ru", "calque",
     r"\b(меняет|изменит|изменил[аио]?) (правила игры|все|всю игру)\b",
     "меняет правила игры (game changer)", "Скажите, что именно изменилось.", 3, False),
    ("ru.calque.seamless", "ru", "calque",
     r"\bбесшовн(ый|ая|ое|ые|о|ой|ую)\b", "бесшовный (seamless)",
     "«Без переключений», «в одном окне», «без ручных шагов».", 2, False),
    ("ru.calque.not_just", "ru", "calque",
     r"\bэто не просто [^.!?\n]{2,60}?,\s*(а|это)\b", "это не просто X, это Y",
     "Оставьте Y. Контраст с воображаемым X ничего не добавляет.", 3, False),
    ("ru.calque.in_the_world_of", "ru", "calque",
     r"\bв мире (маркетинга|бизнеса|технологий|дизайна|контента|нейросетей|ии|финансов|моды|красоты|спорта|образования)\b",
     "в мире маркетинга (in the world of)", "«В маркетинге».", 2, False),
    ("ru.calque.journey", "ru", "calque",
     r"\b(ваше|свое|это|наше) путешеств(ие|ия|ии)\b(?! (в|по|на) )", "ваше путешествие (journey)",
     "«Путь», «работа», или назовите, что человек делает.", 2, False),
    ("ru.calque.insight", "ru", "calque",
     r"\bинсайт(ы|ов|ам|ами|ах)?\b", "инсайт", "«Вывод», «наблюдение», «находка».", 1, False),
    ("ru.calque.landscape", "ru", "calque",
     r"\bландшафт(е|а|у)? (рынка|индустрии|технологий|медиа|угроз)\b", "ландшафт рынка (landscape)",
     "«Рынок», «что есть на рынке».", 2, False),
    ("ru.calque.powerful_tool", "ru", "calque",
     r"\bмощн(ый|ая|ое|ые|ым|ой) (инструмент|решение|платформа|средство|способ)\b", "мощный инструмент",
     "Скажите, что инструмент делает.", 2, False),
    ("ru.calque.whether", "ru", "calque",
     r"\bбудь то [^.!?\n]{3,60}? или\b", "будь то X или Y", "Уберите перечисление или сделайте его конкретным.", 2, False),
    ("ru.calque.at_end_of_day", "ru", "calque",
     r"\bв конце дня,", "в конце дня (at the end of the day)",
     "«В итоге» или уберите.", 2, False),
    ("ru.calque.key_to", "ru", "calque",
     r"\b(ключ|секрет) к (успеху|успешн|эффективн|росту|продаж)", "ключ к успеху",
     "Назовите действие, которое работает.", 2, False),
    ("ru.calque.ecosystem", "ru", "calque",
     r"\bэкосистем(а|ы|е|у|ой)\b", "экосистема", "Перечислите, что входит в набор.", 1, False),
    ("ru.calque.empower", "ru", "calque",
     r"\b(позволя(ет|ют) вам|дает возможность|предоставляет возможность)\b", "позволяет вам",
     "Глагол действия: «вы можете», «вы получаете» или просто действие.", 1, False),

    # ---- hype -------------------------------------------------------------------
    ("ru.hype.unique", "ru", "hype",
     r"\b(уникальн|инновационн|революционн|прорывн|передов|невероятн|потрясающ|феноменальн|непревзойденн)[а-я]+\b",
     "уникальный / инновационный", "Факт вместо оценки: что именно нельзя получить в другом месте.", 2, False),
    ("ru.hype.effective", "ru", "hype",
     r"\b(эффективн|результативн|продуктивн|оптимальн)(ый|ая|ое|ые|о|ость|ости|ым|ых|ую|ой)\b",
     "эффективный", "Насколько, в чём, по сравнению с чем.", 1, False),
    ("ru.hype.ideal", "ru", "hype",
     r"\bидеальн(о|ый|ая|ое|ые|ым|ой|ую) (подходит|решение|вариант|выбор|для)\b", "идеально подходит",
     "Для кого и почему.", 2, False),
    ("ru.hype.complex_approach", "ru", "hype",
     r"\b(комплексн|индивидуальн|персонализированн|клиентоориентированн)(ый|ая|ое|ые|ым|ой|ую) (подход|решени[ея]|сервис|предложени[ея])\b",
     "комплексный подход", "Перечислите, что входит.", 2, False),
    ("ru.hype.wide_range", "ru", "hype",
     r"\bширок(ий|ого|им|ую) (спектр|ассортимент|выбор|набор|круг)\b", "широкий спектр",
     "Назовите число или три главных пункта.", 2, False),
    ("ru.hype.high_quality", "ru", "hype",
     r"\b(высок(ое|ого|им|ий) качеств[ао]|премиальн(ое|ый|ая|ые) качеств[ао]|качественн(ый|ая|ое|ые) (сервис|продукт|контент|результат))\b",
     "высокое качество", "Что именно хорошо: материал, срок, точность.", 2, False),
    ("ru.hype.effortless", "ru", "hype",
     r"\b(без (лишних )?усилий|легко и просто|просто и удобно|быстро и легко|в (пару|несколько|два) клик[ао]в?)\b",
     "без лишних усилий", "Опишите шаги; читатель сам решит, легко ли.", 2, False),
    ("ru.hype.maximum", "ru", "hype",
     r"\bмаксимальн(о|ый|ая|ое|ые|ую) (удобн|эффективн|быстр|простой|прост|комфортн|точн|полезн)[а-я]*\b",
     "максимально удобно", "Уберите «максимально».", 2, False),
    ("ru.hype.key", "ru", "hype",
     r"\bключев(ой|ая|ое|ые|ым|ых|ую|ого) (роль|момент|фактор|аспект|преимуществ|особенност|элемент|показател|задач)[а-я]*\b",
     "ключевой аспект", "«Главный» или уберите прилагательное.", 1, False),
    ("ru.hype.real_breakthrough", "ru", "hype",
     r"\b(настоящ(ий|ая|ее) (прорыв|находка|революция|сокровище)|новое слово в)\b", "настоящий прорыв",
     "Что стало возможно, чего не было раньше.", 2, False),
    ("ru.hype.modern_solution", "ru", "hype",
     r"\bсовременн(ое|ый|ая|ые|ых|ым) (решени[ея]|подход|технологи[ия]|инструмент[ы]?|метод[ы]?)\b", "современное решение",
     "Все решения современные, пока не устарели. Уберите.", 1, False),

    # ---- triplet ------------------------------------------------------------------
    ("ru.triplet.adjectives", "ru", "triplet",
     r"\b[а-я]{3,}(?:ый|ая|ое|ые|ий|яя|ее|ие|ой)\b,\s+[а-я]{3,}(?:ый|ая|ое|ые|ий|яя|ее|ие|ой)\b\s+и\s+[а-я]{3,}(?:ый|ая|ое|ые|ий|яя|ее|ие|ой)\b",
     "три прилагательных подряд", "Оставьте одно, самое точное.", 2, False),
    ("ru.triplet.nouns", "ru", "triplet",
     r"\b[а-я]{4,}(?:ость|ение|ание|ция|сть|ия),\s+[а-я]{4,}(?:ость|ение|ание|ция|сть|ия)\s+и\s+[а-я]{4,}(?:ость|ение|ание|ция|сть|ия)\b",
     "три абстрактных существительных", "Оставьте одно и покажите его на примере.", 2, False),

    # ---- outro --------------------------------------------------------------------
    ("ru.outro.summing_up", "ru", "outro",
     r"\b(в заключение|подводя итог[и]?|резюмируя|в итоге можно сказать|суммируя (вышесказанное|сказанное)|подытожим|подытоживая)[,:]?[ \t]*",
     "подводя итог", "Если вывод новый, напишите его без объявления. Если старый, удалите абзац.", 3, True),
    ("ru.outro.conclude", "ru", "outro",
     r"\b(можно сделать вывод|можно с уверенностью сказать|становится (очевидно|ясно|понятно)), что[ \t]*",
     "можно сделать вывод, что", "Уберите, оставьте вывод.", 3, True),
    ("ru.outro.hope_useful", "ru", "outro",
     r"\b(надеюсь|надеемся),? (что )?(эта |данная )?(статья|информация|пост|материал|это) (была|был|было|будет|окажется) (полезн[аыо]й?|интересн[аыо]й?)[^.!?\n]*[.!?]?",
     "надеюсь, статья была полезной", "Удалите предложение целиком.", 3, True),
    ("ru.outro.remember", "ru", "outro",
     r"\b(помните|не забывайте|главное помнить|важно помнить)[,:]? (что )?", "помните, что",
     "Уберите напоминание; скажите один раз, там, где это уместно.", 2, True),
    ("ru.outro.choice_is_yours", "ru", "outro",
     r"\b(выбор (за вами|остается за вами)|решать (только )?вам|каждый решает сам)[.!]?",
     "выбор за вами", "Удалите. Читатель знает, кто решает.", 2, True),
    ("ru.outro.share", "ru", "outro",
     r"\b(делитесь (в комментариях|своим мнением|опытом)|пишите в комментариях|ставьте лайк|подписывайтесь)\b",
     "делитесь в комментариях", "Один призыв на пост, и только если вам правда нужен ответ.", 1, False),
    ("ru.outro.vyvod_label", "ru", "outro",
     r"^(вывод|итог|итоги|заключение|резюме|в итоге)\s*[:.]\s*$", "абзац с заголовком «Вывод:»",
     "Уберите заголовок; абзац должен выдерживать чтение без подписи.", 2, False),

    # ---- chat ---------------------------------------------------------------------
    ("ru.chat.of_course", "ru", "chat",
     r"^(конечно|отлично|отличный вопрос|хороший вопрос|с удовольствием)[!.,][ \t]*",
     "Конечно! / Отличный вопрос", "Удалите: это ответ чат-боту, а не читателю.", 3, True),
    ("ru.chat.here_are", "ru", "chat",
     r"\bвот (несколько|некоторые|основные|главные|ключевые|список|что) [^.!?\n:]{0,40}[:.][ \t]*",
     "вот несколько вариантов:", "Уберите анонс списка; список говорит сам за себя.", 2, True),
    ("ru.chat.hope_helps", "ru", "chat",
     r"\bнадеюсь, (это|что это) (поможет|помогло|было полезно)[^.!?\n]*[.!?]?",
     "надеюсь, это поможет", "Удалите.", 3, True),
    ("ru.chat.questions", "ru", "chat",
     r"\bесли (у вас )?(есть|остались|возникнут|появятся) (еще |какие-либо |дополнительные )?вопросы\b",
     "если у вас остались вопросы", "Оставьте только с конкретным каналом и временем ответа; иначе удалите.", 1, False),
    ("ru.chat.as_ai", "ru", "chat",
     r"\b(как (ии|искусственный интеллект|языковая модель|нейросеть)|я (всего лишь |только )?(ии|языковая модель|нейросеть))\b",
     "как языковая модель", "Удалите вместе с предложением.", 3, False),
    ("ru.chat.please_note", "ru", "chat",
     r"\b(пожалуйста, )?обратите внимание[,:]? (что )?", "обратите внимание, что",
     "Уберите; если это важно, вынесите в отдельное предложение.", 2, True),
    ("ru.chat.recommend", "ru", "chat",
     r"\b(я бы (рекомендовал|посоветовал|предложил)|рекомендуется|рекомендую вам|советую вам)\b",
     "рекомендуется", "Повелительное наклонение: «сделайте», «проверьте».", 1, False),
    ("ru.chat.additionally_can", "ru", "chat",
     r"\b(дополнительно|также) (вы )?можете\b", "также вы можете", "«Ещё можно» или новый пункт списка.", 1, False),

    # ---- rhetoric ------------------------------------------------------------------
    ("ru.rhetoric.did_you_know", "ru", "rhetoric",
     r"\b(знаете ли вы|а вы знали|задумывались ли вы|вы когда-нибудь задумывались)[^?\n]*\?", "знаете ли вы, что?",
     "Скажите факт утверждением.", 2, False),
    ("ru.rhetoric.spoiler", "ru", "rhetoric",
     r"\bспойлер[:\s]", "спойлер:", "Уберите; просто скажите.", 2, False),
    ("ru.rhetoric.heres_why", "ru", "rhetoric",
     r"\b(и вот почему|и вот как|и вот что (из этого )?(вышло|получилось)|но есть (один )?нюанс|но есть и обратная сторона)[.:]?",
     "и вот почему", "Уберите; следующее предложение и так объясняет.", 2, False),
    ("ru.rhetoric.sounds_familiar", "ru", "rhetoric",
     r"\b(звучит знакомо|знакомо|узнаете себя|правда ведь|согласитесь|не так ли)\?", "звучит знакомо?",
     "Уберите вопрос к читателю.", 2, False),
    ("ru.rhetoric.ready", "ru", "rhetoric",
     r"\b(готовы|поехали|начнем|приступим)[!?]", "Готовы? Поехали!", "Уберите.", 2, False),
    ("ru.rhetoric.not_about", "ru", "rhetoric",
     r"\bэто не (про|о|об) [^.!?\n]{2,40}[.] это (про|о|об)\b", "Это не про X. Это про Y.",
     "Скажите про Y сразу.", 3, False),
    ("ru.rhetoric.you_heard_right", "ru", "rhetoric",
     r"\b(да, вы не ослышались|да-да, именно так|именно так|вы не ослышались)[.!,]", "да, вы не ослышались",
     "Уберите.", 2, False),

    # ======================= English ==========================================
    ("en.intro.todays_world", "en", "intro",
     r"\bin today'?s (?:(?:fast-paced|rapidly (?:changing|evolving)|digital|modern|ever-changing|competitive|interconnected|busy) )*(world|landscape|era|age|society|environment|economy|market)[,]?[ \t]*",
     "in today's fast-paced world", "Delete. Start with the fact.", 3, True),
    ("en.intro.dive_in", "en", "intro",
     r"\b(let'?s|we'?ll|we will) (dive|delve|jump) (in|into|deeper)[^.!?\n]*[.!?:]?[ \t]*", "let's dive in",
     "Delete the invitation and start.", 3, True),
    ("en.intro.in_this_article", "en", "intro",
     r"\bin this (article|post|guide|piece),? (we|you|i)('ll| will)?\b", "in this article we will",
     "Delete the announcement; keep the content.", 2, False),
    ("en.intro.imagine", "en", "intro",
     r"\b(imagine|picture) (this|a world|if)[,:]?[ \t]*", "imagine this:", "Describe the scene directly.", 1, True),
    ("en.filler.important_to_note", "en", "filler",
     r"\bit('?s| is) (important|worth|crucial|essential|vital) to (note|mention|remember|understand|highlight|emphasize|point out) that[ \t]*",
     "it's important to note that", "Delete the frame, keep the note.", 3, True),
    ("en.filler.adverb_connectors", "en", "filler",
     r"\b(moreover|furthermore|additionally|in addition|consequently|ultimately|essentially|notably|importantly|crucially)[,][ \t]*",
     "moreover,", "Delete; adjacent sentences connect on their own.", 1, True),
    ("en.filler.at_end_of_day", "en", "filler",
     r"\bat the end of the day[,]?[ \t]*", "at the end of the day", "Delete.", 2, True),
    ("en.filler.certainly", "en", "filler",
     r"\b(undoubtedly|certainly|without a doubt|needless to say|of course)[,][ \t]*", "undoubtedly,",
     "Delete; prove it or drop it.", 2, True),
    ("en.bureau.utilize", "en", "bureau",
     r"\b(utiliz(e|es|ed|ing)|leverag(e|es|ed|ing)|facilitat(e|es|ed|ing))\b", "utilize / leverage",
     "«use», «run», «help».", 2, False),
    ("en.bureau.in_order_to", "en", "bureau", r"\bin order to\b", "in order to", "«to».", 1, False),
    ("en.bureau.due_to_fact", "en", "bureau", r"\bdue to the fact that\b", "due to the fact that", "«because».", 2, False),
    ("en.calque.delve", "en", "calque",
     r"\bdelv(e|es|ed|ing)\b", "delve", "«look at», «examine», or nothing.", 3, False),
    ("en.calque.tapestry", "en", "calque",
     r"\b(tapestry|testament to|beacon of|symphony of|realm of|cornerstone of)\b", "a testament to",
     "Say what it shows.", 3, False),
    ("en.calque.game_changer", "en", "calque",
     r"\b(game[- ]chang(er|ing)|revolutioniz(e|es|ed|ing)|paradigm shift|next level)\b",
     "game-changer", "Say what changed and by how much.", 3, False),
    ("en.calque.unlock", "en", "calque",
     r"\bunlock (the |your )?(full |true )?(potential|power|value)\b", "unlock the full potential",
     "Name the result.", 3, False),
    ("en.calque.seamless", "en", "calque",
     r"\b(seamless(ly)?|frictionless|effortless(ly)?|streamlined?)\b", "seamless",
     "«in one step», «without switching apps».", 2, False),
    ("en.calque.not_just", "en", "calque",
     r"\b(it'?s |this is |that'?s )?not (just|only|merely) (about )?[^.!?\n]{2,60}?[,;]? (it'?s|but) (about |also )?", "it's not just X, it's Y",
     "Keep Y; drop the imaginary X.", 3, False),
    ("en.calque.navigate", "en", "calque",
     r"\bnavigat(e|es|ed|ing) (the |this |your )?(complex |ever-changing |evolving )?(landscape|world|complexities|challenges|waters)\b",
     "navigate the landscape", "Name the problem.", 3, False),
    ("en.calque.journey", "en", "calque",
     r"\b(embark on|your|this|the) (a )?(journey|adventure)\b", "embark on a journey",
     "«start», «process», or name the task.", 2, False),
    ("en.hype.cutting_edge", "en", "hype",
     r"\b(cutting[- ]edge|state[- ]of[- ]the[- ]art|groundbreaking|innovative|revolutionary|unparalleled|world[- ]class|best[- ]in[- ]class)\b",
     "cutting-edge", "A fact instead of a rating.", 2, False),
    ("en.hype.robust", "en", "hype",
     r"\b(robust|powerful|comprehensive|holistic|vibrant|dynamic|transformative|pivotal|crucial)\b", "robust / powerful",
     "Say what it does.", 1, False),
    ("en.hype.elevate", "en", "hype",
     r"\b(elevat(e|es|ed|ing)|empower(s|ed|ing)?|harness(es|ed|ing)?|foster(s|ed|ing)?|underscor(e|es|ed|ing)|bolster(s|ed|ing)?)\b",
     "elevate / empower", "A plain verb: «improve», «let», «use».", 2, False),
    ("en.hype.whether", "en", "hype",
     r"\bwhether you'?re (a |an )?[^.!?\n]{2,50}? or (a |an )?[^.!?\n]{2,50}?,", "whether you're X or Y,",
     "Delete or name the real audience.", 2, False),
    ("en.triplet.adjectives", "en", "triplet",
     r"\b[a-z]{4,}, [a-z]{4,},? and [a-z]{4,}\b(?= [a-z]+)", "three adjectives in a row",
     "Keep the most precise one.", 2, False),
    ("en.outro.in_conclusion", "en", "outro",
     r"\b(in conclusion|in summary|to sum up|to summarize|all in all|overall)[,:][ \t]*", "in conclusion,",
     "If the conclusion is new, state it; if not, delete the paragraph.", 3, True),
    ("en.outro.hope_helps", "en", "outro",
     r"\b(i hope this helps|hope this helps|hope you found this (useful|helpful))[^.!?\n]*[.!?]?", "I hope this helps",
     "Delete.", 3, True),
    ("en.outro.remember", "en", "outro",
     r"\b(remember|keep in mind|don'?t forget)[,:]? (that )?", "remember that", "Delete the reminder.", 2, True),
    ("en.chat.great_question", "en", "chat",
     r"^(certainly|absolutely|great question|good question|of course|sure)[!.,][ \t]*", "Certainly! / Great question",
     "Delete: it answers a chatbot, not a reader.", 3, True),
    ("en.chat.here_are", "en", "chat",
     r"\bhere (are|is) (some|a few|the|several|key) [^.!?\n:]{0,40}[:.][ \t]*", "here are some tips:",
     "Delete the list announcement.", 2, True),
    ("en.chat.as_ai", "en", "chat",
     r"\bas an? (ai|language model|large language model|llm)\b", "as an AI", "Delete the sentence.", 3, False),
    ("en.chat.please_note", "en", "chat",
     r"\bplease note that[ \t]*", "please note that", "Delete.", 2, True),
    ("en.chat.feel_free", "en", "chat",
     r"\b(feel free to|don'?t hesitate to)\b", "feel free to", "Imperative: «ask», «write».", 2, False),
    ("en.rhetoric.heres_why", "en", "rhetoric",
     r"\b(here'?s why|here'?s the thing|the best part\?|spoiler( alert)?:|sound familiar\?|but here'?s the catch)", "here's why",
     "Delete; the next sentence explains anyway.", 2, False),
    ("en.rhetoric.ever_wondered", "en", "rhetoric",
     r"\b(have you ever wondered|did you know|ever wondered)[^?\n]*\?", "have you ever wondered?",
     "State the fact.", 2, False),
]

PATTERNS = [dict(zip(("id", "lang", "category", "regex", "label", "fix", "weight", "cut"), p)) for p in _P]

_COMPILED = {}


def compiled(pat):
    rx = _COMPILED.get(pat["id"])
    if rx is None:
        flags = re.IGNORECASE | re.MULTILINE
        rx = re.compile(pat["regex"], flags)
        _COMPILED[pat["id"]] = rx
    return rx


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

WORD_RX = re.compile(r"[A-Za-zА-Яа-яЁё0-9][A-Za-zА-Яа-яЁё0-9'’\-]*")
CYR_RX = re.compile(r"[А-Яа-яЁё]")
LAT_RX = re.compile(r"[A-Za-z]")
EMOJI_RX = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF\U00002B00-\U00002BFF✅❌✔✖‼⁉〰〽㊗㊙]"
    "[️]?")
BULLET_RX = re.compile(r"^\s*(?:[-*•▪◦]|\d+[.)])\s+")
BOLD_LEAD_RX = re.compile(r"^\s*(?:[-*•]\s+|\d+[.)]\s+)?\*\*[^*\n]{2,60}?(?::\*\*|\*\*\s*[:—-])")
HEADING_RX = re.compile(r"^\s*#{1,6}\s+")


def fold(text):
    """Lowercase and fold ё->е so one regex covers both spellings."""
    return text.lower().replace("ё", "е")


def word_count(text):
    return len(WORD_RX.findall(text))


def detect_lang(text):
    c, l = len(CYR_RX.findall(text)), len(LAT_RX.findall(text))
    if c == 0 and l == 0:
        return "ru"
    return "ru" if c >= l else "en"


def line_of(offsets, pos):
    """Binary search: 1-based line number for a character offset."""
    lo, hi = 0, len(offsets) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if offsets[mid] <= pos:
            lo = mid
        else:
            hi = mid - 1
    return lo + 1


def line_offsets(text):
    offs = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            offs.append(i + 1)
    return offs


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def find_hits(text, lang):
    """Return a list of hits: dict(id, category, label, fix, weight, line, col, text)."""
    folded = fold(text)
    offs = line_offsets(text)
    hits = []
    for pat in PATTERNS:
        if pat["lang"] != lang:
            continue
        for m in compiled(pat).finditer(folded):
            start, end = m.start(), m.end()
            if end == start:
                continue
            raw = text[start:end].strip()
            ln = line_of(offs, start)
            hits.append({
                "id": pat["id"], "category": pat["category"], "label": pat["label"], "fix": pat["fix"],
                "weight": pat["weight"], "line": ln, "col": start - offs[ln - 1] + 1, "text": raw,
            })
    # The same span can be matched by two patterns (e.g. hype + triplet); keep both, they are different advice.
    hits.sort(key=lambda h: (h["line"], h["col"], h["id"]))
    return hits


def structure_checks(text, lang):
    """Form-level checks that are not phrase regexes. Returns (hits, metrics)."""
    lines = text.split("\n")
    words = max(word_count(text), 1)
    hits = []
    metrics = {}

    emojis = EMOJI_RX.findall(text)
    metrics["emoji"] = len(emojis)
    metrics["emoji_per_100w"] = round(len(emojis) * 100 / words, 1)
    emoji_bullets = sum(1 for l in lines if EMOJI_RX.match(l.strip()[:3]))
    metrics["emoji_bullets"] = emoji_bullets

    dashes = text.count("—") + text.count("–") + len(re.findall(r"\s-\s", text))
    metrics["dashes"] = dashes
    metrics["dashes_per_100w"] = round(dashes * 100 / words, 1)

    bold_leads = sum(1 for l in lines if BOLD_LEAD_RX.match(l))
    metrics["bold_lead_bullets"] = bold_leads

    # longest run of consecutive bullet lines
    run = best = 0
    for l in lines:
        if BULLET_RX.match(l) or EMOJI_RX.match(l.strip()[:3]):
            run += 1
            best = max(best, run)
        elif l.strip():
            run = 0
    metrics["longest_list"] = best

    excl = text.count("!")
    metrics["exclamations"] = excl
    metrics["exclamations_per_100w"] = round(excl * 100 / words, 1)

    headings_with_emoji = sum(1 for l in lines if HEADING_RX.match(l) and EMOJI_RX.search(l))
    metrics["headings_with_emoji"] = headings_with_emoji

    paras = [p for p in re.split(r"\n\s*\n", text) if p.strip() and not BULLET_RX.match(p) and not HEADING_RX.match(p)]
    plens = [word_count(p) for p in paras]
    if len(plens) >= 4:
        mean = sum(plens) / len(plens)
        var = sum((x - mean) ** 2 for x in plens) / len(plens)
        cv = (var ** 0.5) / mean if mean else 0
        metrics["paragraph_cv"] = round(cv, 2)
    else:
        metrics["paragraph_cv"] = None

    def add(sid, label, fix, weight, line=0):
        hits.append({"id": sid, "category": "structure", "label": label, "fix": fix,
                     "weight": weight, "line": line, "col": 0, "text": ""})

    ru = lang == "ru"
    enough = words >= 40  # density checks are meaningless on a two-line note
    if (enough and metrics["emoji_per_100w"] >= 2.0) or emoji_bullets >= 3:
        add("structure.emoji",
            "эмодзи вместо структуры" if ru else "emoji as structure",
            "Оставьте не больше одного на пост, и то не в начале строки." if ru else "At most one per post, never as a bullet.",
            2)
    if enough and metrics["dashes_per_100w"] >= 2.5:
        add("structure.dashes",
            "тире через слово" if ru else "dash in every sentence",
            "Половину тире замените на точку или запятую." if ru else "Replace half of them with a period or comma.",
            2)
    if bold_leads >= 3:
        add("structure.bold_leads",
            "жирный заголовок в каждом пункте" if ru else "bold label in every bullet",
            "Уберите жирные подписи; пункт должен читаться без них." if ru else "Drop the bold labels; a bullet should read without them.",
            2)
    if best >= 7:
        add("structure.list_wall",
            "простыня списка (%d строк подряд)" % best if ru else "list wall (%d bullets in a row)" % best,
            "Сверните в абзац или оставьте 3–5 пунктов." if ru else "Fold into prose or keep 3-5 items.",
            2)
    if enough and metrics["exclamations_per_100w"] >= 2.0:
        add("structure.exclamations",
            "восклицательные знаки" if ru else "exclamation marks",
            "Один на текст, лучше ноль." if ru else "One per text, better none.",
            1)
    if headings_with_emoji:
        add("structure.heading_emoji",
            "эмодзи в заголовках" if ru else "emoji in headings",
            "Заголовок без эмодзи." if ru else "Headings without emoji.",
            1)
    if metrics["paragraph_cv"] is not None and metrics["paragraph_cv"] < 0.2:
        add("structure.uniform_paragraphs",
            "абзацы одинаковой длины" if ru else "paragraphs of identical length",
            "Сделайте один абзац короче, один длиннее; ровный ритм выдаёт генерацию." if ru else "Vary paragraph length; a flat rhythm reads as generated.",
            1)
    return hits, metrics


def score_of(hits, words):
    weighted = sum(h["weight"] for h in hits)
    per100 = weighted * 100 / max(words, 1)
    return min(100, int(round(per100 * 8))), weighted, round(per100, 2)


def verdict(score, lang):
    ru = lang == "ru"
    if score < 10:
        return "чисто" if ru else "clean"
    if score < 30:
        return "лёгкий налёт" if ru else "light"
    if score < 60:
        return "заметно" if ru else "heavy"
    return "читается как бот" if ru else "reads like a bot"


def analyze(text, lang=None):
    lang = lang or detect_lang(text)
    words = word_count(text)
    hits = find_hits(text, lang)
    shits, metrics = structure_checks(text, lang)
    all_hits = hits + shits
    score, weighted, per100 = score_of(all_hits, words)
    by_cat = {}
    for h in all_hits:
        by_cat[h["category"]] = by_cat.get(h["category"], 0) + 1
    return {
        "lang": lang, "words": words, "hits": all_hits, "score": score, "weighted": weighted,
        "per_100_words": per100, "verdict": verdict(score, lang), "by_category": by_cat, "metrics": metrics,
    }


# ---------------------------------------------------------------------------
# strip: safe cuts only
# ---------------------------------------------------------------------------

def strip_text(text, lang=None):
    """Remove phrases whose pattern has cut=True. Returns (new_text, removed_count).

    Only runs on the original text (case preserved) using the folded copy for positions, so
    capitalisation of the remaining sentence start is restored afterwards.
    """
    lang = lang or detect_lang(text)
    folded = fold(text)
    spans = []
    for pat in PATTERNS:
        if pat["lang"] != lang or not pat["cut"]:
            continue
        for m in compiled(pat).finditer(folded):
            if m.end() > m.start():
                spans.append((m.start(), m.end()))
    spans.sort()
    merged = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    out = []
    last = 0
    for s, e in merged:
        out.append(text[last:s])
        # If the cut started a sentence (or a line), capitalise what follows.
        before = "".join(out).rstrip()
        rest = text[e:]
        tail = before.rsplit("\n", 1)[-1]  # what is left on the current line before the cut
        plain = before.rstrip("*_`)\"»")  # ignore closing Markdown/quote marks when looking at the last char
        starts_sentence = (plain == "" or plain[-1] in ".!?\n:" or not WORD_RX.search(tail))
        if starts_sentence and rest[:1].isalpha():
            rest = rest[0].upper() + rest[1:]
            text = text[:e] + rest
        last = e
    out.append(text[last:])
    result = "".join(out)
    # tidy doubled spaces and a comma left hanging at a sentence start
    result = re.sub(r"[ \t]{2,}", " ", result)
    result = re.sub(r"[ \t]+\n", "\n", result)
    result = re.sub(r"\n{3,}", "\n\n", result).lstrip("\n")
    result = re.sub(r"(^|[.!?]\s+)[,;][ \t]*", r"\1", result, flags=re.MULTILINE)
    result = re.sub(r"(^|\n)([а-яёa-z])", lambda m: m.group(1) + m.group(2).upper(), result)
    return result, len(merged)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def read_input(path):
    if path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8") as f:
        return f.read()


def fmt_check(res, name, show_fix=True):
    lines = []
    ru = res["lang"] == "ru"
    lines.append("%s: %d %s, %s %s" % (
        name, res["words"], "слов" if ru else "words", "язык" if ru else "lang", res["lang"]))
    if not res["hits"]:
        lines.append("  " + ("штампов не найдено" if ru else "no patterns found"))
    for h in res["hits"]:
        loc = ("стр. %d" % h["line"]) if ru else ("line %d" % h["line"])
        if h["line"] == 0:
            loc = "текст" if ru else "text"
        shown = h["text"] if h["text"] else h["label"]
        if len(shown) > 48:
            shown = shown[:45] + "..."
        line = "  %-8s [%s] %s" % (loc, h["category"], shown)
        if h["text"] and h["label"] != shown:
            line += "  <- " + h["label"]
        lines.append(line)
        if show_fix:
            lines.append("           " + h["fix"])
    cat = ", ".join("%s %d" % (k, v) for k, v in sorted(res["by_category"].items(), key=lambda kv: -kv[1]))
    lines.append("  %s: %d/100 (%s)%s" % (
        "оценка" if ru else "score", res["score"], res["verdict"], ("; " + cat) if cat else ""))
    return "\n".join(lines)


def fmt_audit(res, name):
    ru = res["lang"] == "ru"
    m = res["metrics"]
    t = lambda a, b: a if ru else b  # noqa: E731
    out = []
    out.append("%s %s" % (t("АУДИТ", "AUDIT"), name))
    out.append("=" * (len(name) + 6))
    out.append("%s: %d   %s: %s   %s: %d/100 (%s)" % (
        t("слов", "words"), res["words"], t("язык", "lang"), res["lang"],
        t("оценка", "score"), res["score"], res["verdict"]))
    out.append("%s: %d (%s %.2f %s)" % (
        t("взвешенных попаданий", "weighted hits"), res["weighted"], t("плотность", "density"),
        res["per_100_words"], t("на 100 слов", "per 100 words")))
    out.append("")
    out.append(t("По категориям", "By category"))
    for key in CATEGORIES:
        n = res["by_category"].get(key, 0)
        if n:
            title = CATEGORIES[key][0] if ru else CATEGORIES[key][1]
            bar = "#" * min(n, 30)
            out.append("  %-10s %-24s %3d  %s" % (key, title, n, bar))
    if not res["by_category"]:
        out.append("  " + t("ничего", "nothing"))
    out.append("")
    out.append(t("Самые частые", "Most frequent"))
    freq = {}
    for h in res["hits"]:
        freq[h["label"]] = freq.get(h["label"], 0) + 1
    for label, n in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:8]:
        out.append("  %2d x %s" % (n, label))
    out.append("")
    out.append(t("Форма", "Form"))
    out.append("  %-22s %s (%s %s)" % (t("эмодзи", "emoji"), m["emoji"], m["emoji_per_100w"], t("на 100 слов", "per 100w")))
    out.append("  %-22s %s (%s %s)" % (t("тире", "dashes"), m["dashes"], m["dashes_per_100w"], t("на 100 слов", "per 100w")))
    out.append("  %-22s %s" % (t("восклицаний", "exclamations"), m["exclamations"]))
    out.append("  %-22s %s" % (t("жирных подписей", "bold labels"), m["bold_lead_bullets"]))
    out.append("  %-22s %s" % (t("длиннейший список", "longest list"), m["longest_list"]))
    out.append("  %-22s %s" % (t("разброс абзацев", "paragraph spread"),
                               "n/a" if m["paragraph_cv"] is None else m["paragraph_cv"]))
    out.append("")
    out.append(t("Что сделать в первую очередь", "Do this first"))
    done = set()
    k = 0
    for h in sorted(res["hits"], key=lambda h: (-h["weight"], h["line"])):
        if h["label"] in done:
            continue
        done.add(h["label"])
        k += 1
        loc = ("" if h["line"] == 0 else " (%s %d)" % (t("стр.", "line"), h["line"]))
        out.append("  %d. %s%s: %s" % (k, h["label"], loc, h["fix"]))
        if k == 5:
            break
    if k == 0:
        out.append("  " + t("ничего: текст чистый", "nothing: the text is clean"))
    return "\n".join(out)


def stats():
    by_lang = {}
    by_cat = {}
    cut = 0
    for p in PATTERNS:
        by_lang[p["lang"]] = by_lang.get(p["lang"], 0) + 1
        by_cat.setdefault(p["lang"], {})
        by_cat[p["lang"]][p["category"]] = by_cat[p["lang"]].get(p["category"], 0) + 1
        cut += 1 if p["cut"] else 0
    struct = 7  # structure checks implemented in structure_checks()
    return {"version": VERSION, "patterns": len(PATTERNS), "by_lang": by_lang, "by_category": by_cat,
            "categories": len(CATEGORIES), "safe_cuts": cut, "structure_checks": struct}


def fmt_stats(s):
    out = ["deslop-ru %s" % s["version"],
           "patterns: %d (ru %d, en %d) + %d structure checks" % (
               s["patterns"], s["by_lang"].get("ru", 0), s["by_lang"].get("en", 0), s["structure_checks"]),
           "categories: %d" % s["categories"],
           "safe cuts (strip mode): %d" % s["safe_cuts"], ""]
    for lang in ("ru", "en"):
        out.append(lang + ":")
        for key in CATEGORIES:
            n = s["by_category"].get(lang, {}).get(key, 0)
            if n:
                out.append("  %-10s %d" % (key, n))
    return "\n".join(out)


def patterns_markdown():
    out = ["# Pattern table", "",
           "Generated by `python3 scripts/deslop.py patterns --markdown`; do not edit by hand. "
           "Weight: 1 light, 2 typical, 3 strong tell. Cut: the `strip` mode may delete the phrase outright.", ""]
    for lang, title in (("ru", "Russian"), ("en", "English")):
        out.append("## %s" % title)
        out.append("")
        for key, (ru_t, en_t, desc) in CATEGORIES.items():
            rows = [p for p in PATTERNS if p["lang"] == lang and p["category"] == key]
            if not rows:
                continue
            out.append("### %s: %s" % (key, ru_t if lang == "ru" else en_t))
            out.append("")
            out.append(desc)
            out.append("")
            out.append("| id | pattern | fix | w | cut |")
            out.append("|---|---|---|:-:|:-:|")
            for p in rows:
                out.append("| `%s` | %s | %s | %d | %s |" % (
                    p["id"], p["label"].replace("|", "\\|"), p["fix"].replace("|", "\\|"), p["weight"],
                    "yes" if p["cut"] else ""))
            out.append("")
        out.append("### structure: %s" % ("Структура" if lang == "ru" else "Structure"))
        out.append("")
        out.append(CATEGORIES["structure"][2])
        out.append("")
        out.append("| check | triggers when |")
        out.append("|---|---|")
        out.append("| emoji | 2+ emoji per 100 words, or 3+ lines that start with an emoji |")
        out.append("| dashes | 2.5+ dashes (—, –, ` - `) per 100 words |")
        out.append("| bold_leads | 3+ bullets that open with a bold label and a colon |")
        out.append("| list_wall | 7+ consecutive bullet lines |")
        out.append("| exclamations | 2+ exclamation marks per 100 words |")
        out.append("| heading_emoji | any Markdown heading containing an emoji |")
        out.append("| uniform_paragraphs | 4+ paragraphs with length spread (coefficient of variation) under 0.2 |")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="deslop.py",
        description="Flag AI-writing patterns (ИИ-штампы) in Russian or English text. Zero dependencies.")
    ap.add_argument("--version", action="version", version="deslop-ru " + VERSION)
    sub = ap.add_subparsers(dest="cmd")

    def common(p):
        p.add_argument("files", nargs="*", default=["-"], help="text or Markdown files; '-' reads stdin")
        p.add_argument("--lang", choices=["ru", "en", "auto"], default="auto")
        p.add_argument("--json", action="store_true", help="machine-readable output")

    pc = sub.add_parser("check", help="list hits with line numbers and a score (default)")
    common(pc)
    pc.add_argument("--no-fix", action="store_true", help="hide the fix hints")
    pc.add_argument("--fail-over", type=int, default=None, metavar="N", help="exit 1 if score > N")

    pa = sub.add_parser("audit", help="category breakdown, structure metrics, verdict, next steps")
    common(pa)
    pa.add_argument("--fail-over", type=int, default=None, metavar="N", help="exit 1 if score > N")

    ps = sub.add_parser("strip", help="remove phrases that can be cut without changing meaning")
    common(ps)
    ps.add_argument("--in-place", action="store_true", help="write the result back to the file")

    pst = sub.add_parser("stats", help="pattern counts per language and category")
    pst.add_argument("--json", action="store_true")

    pp = sub.add_parser("patterns", help="dump the pattern table")
    pp.add_argument("--markdown", action="store_true", help="Markdown (default is JSON)")

    args = ap.parse_args(argv)
    cmd = args.cmd or "check"

    if cmd == "stats":
        s = stats()
        print(json.dumps(s, ensure_ascii=False, indent=2) if args.json else fmt_stats(s))
        return 0
    if cmd == "patterns":
        if args.markdown:
            sys.stdout.write(patterns_markdown())
        else:
            print(json.dumps(PATTERNS, ensure_ascii=False, indent=2))
        return 0

    lang = None if args.lang == "auto" else args.lang
    worst = 0
    results = []
    for path in args.files:
        text = unicodedata.normalize("NFC", read_input(path))
        name = "stdin" if path == "-" else path
        if cmd == "strip":
            new, n = strip_text(text, lang)
            if args.in_place and path != "-":
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new)
                print("%s: removed %d phrase(s)" % (name, n))
            else:
                sys.stdout.write(new)
            continue
        res = analyze(text, lang)
        worst = max(worst, res["score"])
        if args.json:
            results.append(dict(res, file=name))
        elif cmd == "audit":
            print(fmt_audit(res, name))
        else:
            print(fmt_check(res, name, show_fix=not args.no_fix))
        if len(args.files) > 1 and not args.json:
            print()
    if args.json and cmd != "strip":
        print(json.dumps(results if len(results) > 1 else results[0], ensure_ascii=False, indent=2))
    if cmd in ("check", "audit") and args.fail_over is not None and worst > args.fail_over:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
