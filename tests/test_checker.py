"""Unit tests for scripts/deslop.py: pattern hits, no false positives on clean text, strip, score, CLI."""
import io
import json
import os
import re
import subprocess
import sys
import unittest
from contextlib import redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import deslop  # noqa: E402

SCRIPT = os.path.join(ROOT, "scripts", "deslop.py")

# (text, pattern id that must fire)
POSITIVE = [
    ("В современном мире каждый бизнес нуждается в сайте.", "ru.intro.modern_world"),
    ("В эпоху цифровых технологий, когда всё меняется, важно быть гибким.", "ru.intro.epoch"),
    ("Давайте разберёмся, как это работает.", "ru.intro.lets_figure"),
    ("Ни для кого не секрет, что кофе бодрит.", "ru.intro.no_secret"),
    ("На сегодняшний день это лучший вариант.", "ru.intro.nowadays"),
    ("Важно отметить, что сроки сдвинулись.", "ru.filler.important_to_note"),
    ("Безусловно, это удобно.", "ru.filler.obviously"),
    ("Таким образом, план готов.", "ru.filler.thus"),
    ("Данный подход работает.", "ru.bureau.dannyj"),
    ("Мы осуществляем доставку.", "ru.bureau.osushchestvlyat"),
    ("Сервис является лидером.", "ru.bureau.yavlyaetsya"),
    ("В рамках проекта мы сделали сайт.", "ru.bureau.v_ramkah"),
    ("Товар представляет собой набор.", "ru.bureau.predstavlyaet_soboj"),
    ("Давайте погрузимся в тему.", "ru.calque.dive_in"),
    ("Выведите бизнес на новый уровень.", "ru.calque.next_level"),
    ("Курс раскроет ваш потенциал.", "ru.calque.unlock_potential"),
    ("Это меняет правила игры.", "ru.calque.game_changer"),
    ("Это не просто кофе, а ритуал.", "ru.calque.not_just"),
    ("Бесшовная интеграция с CRM.", "ru.calque.seamless"),
    ("Уникальное предложение для вас.", "ru.hype.unique"),
    ("Идеально подходит для семьи.", "ru.hype.ideal"),
    ("Широкий спектр услуг.", "ru.hype.wide_range"),
    ("Быстрый, удобный и надёжный сервис.", "ru.triplet.adjectives"),
    ("Подводя итог, скажу одно.", "ru.outro.summing_up"),
    ("Надеюсь, эта статья была полезной.", "ru.outro.hope_useful"),
    ("Помните, что всё в ваших руках.", "ru.outro.remember"),
    ("Конечно! Вот план.", "ru.chat.of_course"),
    ("Вот несколько советов: пейте воду.", "ru.chat.here_are"),
    ("Надеюсь, это поможет!", "ru.chat.hope_helps"),
    ("Обратите внимание, что цены изменились.", "ru.chat.please_note"),
    ("Знаете ли вы, что кошки спят 16 часов?", "ru.rhetoric.did_you_know"),
    ("Спойлер: это не сработало.", "ru.rhetoric.spoiler"),
    ("Звучит знакомо?", "ru.rhetoric.sounds_familiar"),
    ("In today's fast-paced digital world, speed matters.", "en.intro.todays_world"),
    ("Let's dive in!", "en.intro.dive_in"),
    ("It's important to note that prices changed.", "en.filler.important_to_note"),
    ("We delve into the data.", "en.calque.delve"),
    ("This is a testament to our team.", "en.calque.tapestry"),
    ("It's not just a tool, it's a platform.", "en.calque.not_just"),
    ("Unlock the full potential of your data.", "en.calque.unlock"),
    ("In conclusion, buy it.", "en.outro.in_conclusion"),
    ("Certainly! Here is the plan.", "en.chat.great_question"),
    ("As an AI language model, I cannot.", "en.chat.as_ai"),
    ("Have you ever wondered why?", "en.rhetoric.ever_wondered"),
]

# clean sentences that must produce zero phrase hits
NEGATIVE = [
    "По данным опроса, 40% респондентов выбрали второй вариант.",
    "Данные хранятся на сервере в Нидерландах.",
    "В данный момент сервер перезагружается.",
    "Мы встретились в конце дня и обсудили бюджет.",
    "Путешествие по Грузии заняло десять дней.",
    "Экспорт в PDF занимает четыре секунды вместо сорока.",
    "Пачка 250 г, зип-лок с клапаном, дата обжарки на пачке.",
    "Поезд отправляется в 7:40 с третьего пути.",
    "The train leaves at 7:40 from platform three.",
    "We fixed the double notification bug in version 2.4.1.",
    "Прежде всего проверьте кабель, потом драйвер.",
    "Не забудьте паспорт.",
    "Хороший вопрос задали на встрече вчера.",
]


class TestPatterns(unittest.TestCase):
    def test_every_regex_compiles(self):
        for p in deslop.PATTERNS:
            re.compile(p["regex"], re.I | re.M)

    def test_ids_unique_and_well_formed(self):
        ids = [p["id"] for p in deslop.PATTERNS]
        self.assertEqual(len(ids), len(set(ids)))
        for p in deslop.PATTERNS:
            self.assertRegex(p["id"], r"^(ru|en)\.[a-z]+\.[a-z0-9_]+$")
            self.assertEqual(p["id"].split(".")[0], p["lang"])
            self.assertEqual(p["id"].split(".")[1], p["category"])
            self.assertIn(p["category"], deslop.CATEGORIES)
            self.assertIn(p["weight"], (1, 2, 3))
            self.assertTrue(p["fix"].strip())

    def test_every_category_has_patterns_in_both_languages(self):
        for cat in deslop.CATEGORIES:
            if cat == "structure":
                continue
            for lang in ("ru", "en"):
                self.assertTrue(any(p["category"] == cat and p["lang"] == lang for p in deslop.PATTERNS),
                                "%s/%s" % (lang, cat))

    def test_positive_samples(self):
        for text, pid in POSITIVE:
            lang = pid.split(".")[0]
            ids = {h["id"] for h in deslop.find_hits(text, lang)}
            self.assertIn(pid, ids, "%r did not trigger %s (got %s)" % (text, pid, sorted(ids)))

    def test_negative_samples(self):
        for text in NEGATIVE:
            hits = deslop.find_hits(text, deslop.detect_lang(text))
            self.assertEqual(hits, [], "%r -> %s" % (text, [h["id"] for h in hits]))

    def test_yo_folding(self):
        self.assertTrue(deslop.find_hits("Давайте разберёмся.", "ru"))
        self.assertTrue(deslop.find_hits("Давайте разберемся.", "ru"))

    def test_line_numbers(self):
        hits = deslop.find_hits("Первая строка.\n\nВажно отметить, что третья.\n", "ru")
        self.assertEqual(hits[0]["line"], 3)
        self.assertEqual(hits[0]["col"], 1)


class TestStructure(unittest.TestCase):
    def test_short_text_has_no_density_hits(self):
        res = deslop.analyze("Привет! Как дела?")
        self.assertEqual(res["hits"], [])
        self.assertEqual(res["score"], 0)

    def test_emoji_bullets_and_list_wall(self):
        text = "\n".join("✅ пункт номер %d про что-то" % i for i in range(8))
        ids = {h["id"] for h in deslop.analyze(text)["hits"]}
        self.assertIn("structure.emoji", ids)
        self.assertIn("structure.list_wall", ids)

    def test_bold_leads_numbered(self):
        text = "\n".join("%d. **Пункт %d:** описание пункта" % (i, i) for i in range(1, 5))
        ids = {h["id"] for h in deslop.analyze(text)["hits"]}
        self.assertIn("structure.bold_leads", ids)


class TestScore(unittest.TestCase):
    def test_bands(self):
        self.assertEqual(deslop.verdict(0, "ru"), "чисто")
        self.assertEqual(deslop.verdict(9, "en"), "clean")
        self.assertEqual(deslop.verdict(10, "en"), "light")
        self.assertEqual(deslop.verdict(30, "en"), "heavy")
        self.assertEqual(deslop.verdict(60, "ru"), "читается как бот")

    def test_formula(self):
        hits = [{"weight": 2}, {"weight": 3}]
        score, weighted, per100 = deslop.score_of(hits, 100)
        self.assertEqual((score, weighted, per100), (40, 5, 5.0))
        self.assertEqual(deslop.score_of([{"weight": 3}] * 50, 100)[0], 100)

    def test_detect_lang(self):
        self.assertEqual(deslop.detect_lang("Привет, world"), "ru")
        self.assertEqual(deslop.detect_lang("Hello, мир and more words"), "en")
        self.assertEqual(deslop.detect_lang(""), "ru")


class TestStrip(unittest.TestCase):
    def test_capitalises_after_cut(self):
        out, n = deslop.strip_text("Важно отметить, что сроки сдвинулись.", "ru")
        self.assertEqual(out, "Сроки сдвинулись.")
        self.assertEqual(n, 1)

    def test_keeps_paragraph_break(self):
        out, _ = deslop.strip_text("Let's dive in!\n\nFirst point.", "en")
        self.assertEqual(out, "First point.")
        out, _ = deslop.strip_text("Intro line. Let's dive in!\n\nFirst point.", "en")
        self.assertEqual(out, "Intro line.\n\nFirst point.")

    def test_capitalises_after_markdown_bold(self):
        out, _ = deslop.strip_text("**1. Шаг.** Обратите внимание, что цены выросли.", "ru")
        self.assertEqual(out, "**1. Шаг.** Цены выросли.")

    def test_never_touches_facts(self):
        text = "Цена 1 990 ₽, доставка 2 дня, гарантия 24 месяца."
        self.assertEqual(deslop.strip_text(text, "ru")[0], text)

    def test_only_cut_patterns(self):
        text = "Уникальное предложение в рамках акции."
        self.assertEqual(deslop.strip_text(text, "ru")[0], text)


class TestCli(unittest.TestCase):
    def run_cli(self, *args, stdin=None):
        return subprocess.run([sys.executable, SCRIPT] + list(args), input=stdin, capture_output=True,
                              text=True, cwd=ROOT, timeout=20)

    def test_help_for_every_subcommand(self):
        for sub in ("", "check", "audit", "strip", "stats", "patterns"):
            args = ([sub] if sub else []) + ["--help"]
            r = self.run_cli(*args)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("usage", r.stdout.lower())

    def test_stdin_and_json(self):
        r = self.run_cli("check", "--json", "-", stdin="Важно отметить, что всё хорошо.\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["file"], "stdin")
        self.assertEqual(data["hits"][0]["id"], "ru.filler.important_to_note")

    def test_fail_over(self):
        r = self.run_cli("check", "--fail-over", "10", "examples/telegram-post.before.md")
        self.assertEqual(r.returncode, 1)
        r = self.run_cli("check", "--fail-over", "10", "examples/telegram-post.after.md")
        self.assertEqual(r.returncode, 0)

    def test_stats_matches_table(self):
        s = deslop.stats()
        self.assertEqual(s["patterns"], len(deslop.PATTERNS))
        self.assertEqual(s["by_lang"]["ru"] + s["by_lang"]["en"], s["patterns"])
        self.assertEqual(s["safe_cuts"], sum(1 for p in deslop.PATTERNS if p["cut"]))
        self.assertEqual(s["categories"], len(deslop.CATEGORIES))

    def test_patterns_markdown_lists_every_id(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            deslop.main(["patterns", "--markdown"])
        md = buf.getvalue()
        for p in deslop.PATTERNS:
            self.assertIn("`%s`" % p["id"], md)


if __name__ == "__main__":
    unittest.main()
