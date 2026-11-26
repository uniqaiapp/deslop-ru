"""The generated site: docs/ is current, SEO limits hold, uniqai.app links are tagged, the page passes its own checker,
and the in-browser checker matches the Python one."""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import deslop  # noqa: E402

_spec = importlib.util.spec_from_file_location("dr_site", os.path.join(ROOT, "scripts", "site.py"))
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)

DOCS = os.path.join(ROOT, "docs")
ALLOWED = {"/", "/chat", "/tools", "/models", "/image/text-to-image", "/tools/ai-prompt-generator", "/detect/ai-text-detector", "/detect"}


def pages():
    out = {}
    for d, _, names in os.walk(DOCS):
        for n in names:
            if n.endswith(".html") and n != "404.html":
                p = os.path.join(d, n)
                out[os.path.relpath(p, DOCS)] = open(p, encoding="utf-8").read()
    return out


def meta(h, name):
    m = re.search(r'<meta name="%s" content="([^"]*)"' % name, h)
    return m.group(1) if m else ""


def visible_ru(h):
    """Our own Russian copy: no quoted material (code, marks, pre, «…»), no English block, no chrome that only lists names."""
    h = re.sub(r"<(script|style|pre|code|mark|noscript)\b.*?</\1>", " ", h, flags=re.S)
    h = re.sub(r'<div class="dr-en".*?</div>', " ", h, flags=re.S)
    h = re.sub(r"<table.*?</table>", " ", h, flags=re.S)
    h = re.sub(r"<(head|header|nav)\b.*?</\1>", " ", h, flags=re.S)
    h = re.sub(r'<ul class="ug-list">.*?</ul>', " ", h, flags=re.S)
    h = re.sub(r"<[^>]+>", " ", h)
    import html as _h
    h = _h.unescape(h)
    h = re.sub(r"«[^»]*»", " ", h)
    return re.sub(r"[ \t]+", " ", h)


class TestSite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = pages()

    def test_docs_up_to_date(self):
        self.assertEqual(subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "site.py"), "--check"], capture_output=True, text=True).returncode, 0)

    def test_page_count_and_files(self):
        self.assertEqual(len(self.pages), 10)
        for f in ("llms.txt", "sitemap.xml", "robots.txt", ".nojekyll", "404.html", "site.css", "site.js", "checker.js", S.INDEXNOW_KEY + ".txt"):
            self.assertTrue(os.path.exists(os.path.join(DOCS, f)), f)
        self.assertEqual(open(os.path.join(DOCS, S.INDEXNOW_KEY + ".txt")).read(), S.INDEXNOW_KEY)

    def test_seo_limits(self):
        titles, descs = set(), set()
        for p, h in self.pages.items():
            t = re.search(r"<title>(.*?)</title>", h).group(1)
            d = meta(h, "description")
            self.assertLessEqual(len(t), 60, p)
            self.assertTrue(t.endswith(" | deslop-ru"), p)
            self.assertTrue(100 <= len(d) <= 150, "%s %d" % (p, len(d)))
            self.assertEqual(h.count("<h1>"), 1, p)
            titles.add(t)
            descs.add(d)
        self.assertEqual(len(titles), len(self.pages))
        self.assertEqual(len(descs), len(self.pages))

    def test_answer_blocks(self):
        for p, h in self.pages.items():
            m = re.search(r'<p class="ug-answer">(.*?)</p>', h)
            self.assertTrue(m, p)
            self.assertTrue(40 <= len(re.sub("<[^>]+>", "", m.group(1)).split()) <= 60, p)

    def test_faqpage_only_on_home(self):
        for p, h in self.pages.items():
            self.assertEqual("FAQPage" in h, p == "index.html", p)
        self.assertIn("<details><summary>", self.pages["index.html"])

    def test_jsonld_parses(self):
        for p, h in self.pages.items():
            for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
                json.loads(m.group(1))

    def test_uniqai_links_tagged(self):
        n = 0
        for p, h in self.pages.items():
            for m in re.finditer(r'<a [^>]*href="(https://uniqai\.app[^"]*)"[^>]*>', h):
                n += 1
                url = m.group(1).replace("&amp;", "&")
                self.assertIn("utm_source=github&utm_medium=pages&utm_campaign=deslop-ru", url, p)
                self.assertIn("data-out=", m.group(0), p)
                self.assertNotIn("nofollow", m.group(0), p)
                self.assertIn(re.match(r"https://uniqai\.app(/[^?]*)", url).group(1), ALLOWED, p)
        self.assertGreater(n, 10)

    def test_no_false_model_claims(self):
        for p, h in self.pages.items():
            text = re.sub("<[^>]+>", " ", h)
            for m in re.finditer(r"UniqAI[^.]{0,80}(Flux|Midjourney|SDXL|Wan|Seedance|Runway|Sora)", text):
                self.fail("%s: %s" % (p, m.group(0)))

    def test_example_pages_have_real_scores(self):
        for slug, b in S.load_examples().items():
            h = self.pages[os.path.join("examples", slug, "index.html")]
            rb, ra = deslop.analyze(b["before"]), deslop.analyze(b["after"])
            self.assertIn("%d/100" % rb["score"], h)
            self.assertIn("%d/100" % ra["score"], h)
            self.assertGreater(rb["score"], ra["score"], slug)

    def test_privacy_author_sister(self):
        for p, h in self.pages.items():
            self.assertIn("никуда не отправляется", h, p)
            self.assertIn("Vlad Yasinski", h, p)
            self.assertIn("https://github.com/hablamusic", h, p)
            self.assertIn("https://www.linkedin.com/in/vlad-yasinski-ua5er/", h, p)
        self.assertIn("в вашем браузере", self.pages["index.html"])

    def test_pattern_anchors(self):
        h = self.pages[os.path.join("patterns", "index.html")]
        for p in deslop.PATTERNS:
            self.assertIn('id="p-%s"' % p["id"].replace(".", "-"), h, p["id"])

    def test_no_em_dashes_in_visible_copy(self):
        for p, h in self.pages.items():
            self.assertNotIn("—", visible_ru(h), p)

    def test_site_passes_its_own_checker(self):
        for p, h in self.pages.items():
            r = deslop.analyze(visible_ru(h), "ru")
            self.assertLess(r["score"], 10, "%s: %s" % (p, [(x["label"], x["text"]) for x in r["hits"]]))
            self.assertEqual([x for x in r["hits"] if x["category"] != "structure"], [], p)


EDGE = [
    "", "   ", "Привет.",
    "В современном мире важно отметить, что данный подход осуществляет широкий спектр задач. Давайте погрузимся в тему!",
    "Let's dive in. This game-changer offers a seamless, robust solution that will unlock your potential. In today's fast-paced world, it's important to note that we leverage cutting-edge tech.",
    "Ёлка, ёж. Важно отметить, ЧТО Ёжик ПРЕДСТАВЛЯЕТ СОБОЙ ёлку. " * 6,
    "Кофе ☕ — это не просто напиток 🚀 — это ритуал ✨!\n\n**Вкус** — богатый.\n**Аромат** — яркий.\n**Цена** — низкая.\n\n## 🔥 Итог\n",
    "\n".join("- пункт %d" % i for i in range(9)) + "\n\nНа сегодняшний день, безусловно, таким образом, это работает. " * 3,
    "Тест. " * 50, "İstanbul ışık Straße ǅ Ǆ — слово слово слово. " * 10,
    "Мы продаём рюкзак на 22 литра, 860 грамм, молнии YKK, гарантия два года. Пишите в чат, ответим в течение часа.\n\nВторой абзац такой же длины, как первый, на самом деле почти такой же.\n\nТретий абзац такой же длины.\n\nЧетвёртый абзац такой же длины.\n\n",
]


@unittest.skipUnless(shutil.which("node"), "node not installed")
class TestParity(unittest.TestCase):
    def test_js_matches_python(self):
        ex = S.load_examples()
        texts = []
        for b in ex.values():
            texts += [b["before"], b["after"]]
        texts += EDGE
        out = subprocess.run(["node", os.path.join(ROOT, "tests", "parity.js")], input=json.dumps({"data": S.data_json(ex), "texts": texts}),
                             capture_output=True, text=True, check=True).stdout
        res = json.loads(out)
        self.assertEqual(len(res), len(texts))
        for text, got in zip(texts, res):
            py, js = deslop.analyze(text), got["result"]
            tag = repr(text[:50])
            for k in ("lang", "words", "score", "weighted", "per_100_words", "verdict"):
                self.assertEqual(js[k], py[k], "%s %s" % (tag, k))
            self.assertEqual(js["by_category"], py["by_category"], tag)

            def key(h):
                return (h["id"], h["line"], h["col"], h["text"], h["weight"], h["category"])
            self.assertEqual(sorted(key(h) for h in js["hits"]), sorted(key(h) for h in py["hits"]), tag)
            st, n = deslop.strip_text(text)
            self.assertEqual(got["strip"]["text"], st, tag)
            self.assertEqual(got["strip"]["removed"], n, tag)
            self.assertIn("np-score", got["html"]) if text.strip() else None


if __name__ == "__main__":
    unittest.main()
