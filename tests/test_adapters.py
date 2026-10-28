"""Structure and forbidden-string checks shared by every uniqaiapp repo (CONVENTIONS.md sections 3.7 and 10)."""
import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "deslop-ru"

FORBIDDEN = [
    "aeoria", "richpeach", "/Users/", "/Volumes/", "node_modules", "sk-ant-", "sk_live",
    "api_key=", "API_KEY=<real", "TODO: fill", "lorem ipsum",
]
TEXT_EXT = {".md", ".py", ".json", ".yml", ".yaml", ".mdc", ".svg", ".txt", ".cff", ".gitignore",
            ".gitattributes", ".editorconfig", ""}
SKIP_DIRS = {".git", "__pycache__"}


def tracked_text_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            ext = os.path.splitext(fn)[1]
            if ext in TEXT_EXT or fn.startswith("."):
                p = os.path.join(dirpath, fn)
                if os.path.getsize(p) < 2_000_000:
                    yield p


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, "SKILL.md has no YAML frontmatter"
    fm = {}
    for line in m.group(1).split("\n"):
        if line.startswith("  ") or not line.strip():
            continue
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip()
    sub = re.search(r"\n  version: ([0-9.]+)", m.group(1))
    fm["metadata.version"] = sub.group(1) if sub else None
    return fm


class TestSkillFrontmatter(unittest.TestCase):
    def setUp(self):
        self.fm = frontmatter(read("SKILL.md"))

    def test_name_equals_repo(self):
        self.assertEqual(self.fm["name"], REPO)
        self.assertEqual(os.path.basename(ROOT), REPO)

    def test_description_single_line_and_length(self):
        d = self.fm["description"]
        self.assertTrue(1 <= len(d) <= 1024, len(d))
        self.assertNotIn("\n", d)
        for trigger in ("AI slop", "ИИ-штампы", "очеловечить", "Not for"):
            self.assertIn(trigger, d)

    def test_versions_match(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("deslop", os.path.join(ROOT, "scripts", "deslop.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        plugin = json.loads(read(".claude-plugin/plugin.json"))
        changelog_top = re.search(r"^## \[([0-9.]+)\]", read("CHANGELOG.md"), re.M).group(1)
        self.assertEqual(self.fm["metadata.version"], plugin["version"])
        self.assertEqual(plugin["version"], changelog_top)
        self.assertEqual(plugin["version"], mod.VERSION)
        self.assertEqual(plugin["name"], REPO)
        self.assertEqual(plugin["skills"], ["./"])

    def test_body_under_500_lines(self):
        self.assertLess(read("SKILL.md").count("\n"), 500)


class TestAdapters(unittest.TestCase):
    def test_cursor_rule(self):
        t = read(".cursor/rules/%s.mdc" % REPO)
        self.assertIn("@SKILL.md", t)
        self.assertTrue(t.startswith("---\ndescription:"))

    def test_agents_and_codex_mention_skill(self):
        self.assertIn("SKILL.md", read("AGENTS.md"))
        self.assertIn("SKILL.md", read("codex/INSTRUCTIONS.md"))

    def test_required_files_exist(self):
        for rel in ("README.md", "README.ru.md", "README.zh-CN.md", "README.es.md", "README.pt-BR.md",
                    "README.ja.md", "README.ko.md", "LICENSE", "CONTRIBUTING.md", "CHANGELOG.md",
                    "CODE_OF_CONDUCT.md", "SECURITY.md", ".gitignore", ".gitattributes", ".editorconfig",
                    ".github/workflows/ci.yml", ".github/ISSUE_TEMPLATE/bug_report.md",
                    ".github/ISSUE_TEMPLATE/feature_request.md", ".github/ISSUE_TEMPLATE/config.yml",
                    ".github/PULL_REQUEST_TEMPLATE.md", ".github/repo.json",
                    "assets/banner.svg", "assets/banner-light.svg", "assets/demo.svg",
                    "assets/social-preview.png", "assets/icon.svg",
                    "examples/README.md", "references/patterns.md", "references/rewrite-guide.md"):
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)

    def test_repo_json(self):
        meta = json.loads(read(".github/repo.json"))
        self.assertEqual(meta["name"], REPO)
        self.assertIn("utm_campaign=" + REPO, meta["homepage"])
        self.assertTrue(5 <= len(meta["topics"]) <= 20)
        self.assertIn("russian", meta["topics"])

    def test_asset_sizes(self):
        limits = {"assets/banner.svg": 15_000, "assets/banner-light.svg": 15_000,
                  "assets/demo.svg": 20_000, "assets/social-preview.png": 120_000, "assets/icon.svg": 4_000}
        for rel, cap in limits.items():
            self.assertLessEqual(os.path.getsize(os.path.join(ROOT, rel)), cap, rel)


class TestForbiddenStrings(unittest.TestCase):
    def test_no_forbidden_strings(self):
        bad = []
        for p in tracked_text_files():
            try:
                with open(p, encoding="utf-8") as f:
                    text = f.read()
            except UnicodeDecodeError:
                continue
            rel = os.path.relpath(p, ROOT)
            low = text.lower()
            for s in FORBIDDEN:
                if s.lower() in low:
                    if rel.startswith("tests/") and s in text and "FORBIDDEN" in text:
                        continue  # this file lists the strings
                    for ln, line in enumerate(text.split("\n"), 1):
                        if s.lower() in line.lower() and "conventions-allow: abs-path" not in line:
                            bad.append("%s:%d: %s" % (rel, ln, s))
        self.assertEqual(bad, [])

    def test_copyright_lines_are_brand_only(self):
        for p in tracked_text_files():
            try:
                with open(p, encoding="utf-8") as f:
                    for line in f:
                        if line.lstrip().startswith("Copyright (c)"):
                            self.assertIn("UniqAI", line, p)
            except UnicodeDecodeError:
                pass


READMES = (("README.md", "readme"), ("README.ru.md", "readme-ru"), ("README.zh-CN.md", "readme-zh-cn"),
           ("README.es.md", "readme-es"), ("README.pt-BR.md", "readme-pt-br"), ("README.ja.md", "readme-ja"),
           ("README.ko.md", "readme-ko"))


class TestReadmeLinks(unittest.TestCase):
    def test_utm_on_every_uniqai_link(self):
        for rel, medium in READMES:
            t = read(rel)
            links = re.findall(r"https://uniqai\.app[^\s\")<>]*", t)
            self.assertTrue(links, rel)
            for l in links:
                self.assertIn("utm_source=github", l, l)
                self.assertIn("utm_medium=" + medium, l, l)
                self.assertIn("utm_campaign=" + REPO, l, l)
            self.assertLessEqual(len(set(links)), 3, rel)
            self.assertEqual(t.count("Made by"), 1, rel)

    def test_readme_relative_links_resolve(self):
        t = "".join(read(rel) for rel, _ in READMES)
        for target in set(re.findall(r"\]\(((?!https?://|#|mailto:)[^)\s]+)\)", t)):
            self.assertTrue(os.path.exists(os.path.join(ROOT, target.split("#")[0])), target)
        for src in set(re.findall(r'src="((?!https?://)[^"]+)"', t)):
            self.assertTrue(os.path.exists(os.path.join(ROOT, src)), src)


if __name__ == "__main__":
    unittest.main()
