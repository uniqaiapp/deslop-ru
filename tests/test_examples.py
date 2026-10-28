"""Every committed example output reproduces byte for byte, and every number in the READMEs comes from the script."""
import io
import os
import re
import sys
import unittest
from contextlib import redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import deslop  # noqa: E402

EX = os.path.join(ROOT, "examples")
NAMES = sorted(f[:-len(".before.md")] for f in os.listdir(EX) if f.endswith(".before.md"))


def run(argv):
    buf = io.StringIO()
    cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        with redirect_stdout(buf):
            deslop.main(argv)
    finally:
        os.chdir(cwd)
    return buf.getvalue()


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


class TestExamplesReproduce(unittest.TestCase):
    def test_there_are_examples(self):
        self.assertGreaterEqual(len(NAMES), 5)
        for n in NAMES:
            self.assertTrue(os.path.exists(os.path.join(EX, n + ".after.md")), n)

    def test_reports_match(self):
        for n in NAMES:
            before = "examples/%s.before.md" % n
            self.assertEqual(run(["check", "--no-fix", before]), read("examples/reports/%s.check.txt" % n), n)
            self.assertEqual(run(["audit", before]), read("examples/reports/%s.audit.txt" % n), n)
            self.assertEqual(run(["strip", before]), read("examples/reports/%s.strip.md" % n), n)

    def test_scores_file_matches(self):
        lines = []
        for n in NAMES:
            for kind in ("before", "after"):
                rel = "examples/%s.%s.md" % (n, kind)
                res = deslop.analyze(read(rel))
                lines.append("%-36s %3d/100  %s" % (rel, res["score"], res["verdict"]))
        self.assertEqual("\n".join(lines) + "\n", read("examples/reports/scores.txt"))

    def test_before_is_slop_and_after_is_clean(self):
        for n in NAMES:
            before = deslop.analyze(read("examples/%s.before.md" % n))
            after = deslop.analyze(read("examples/%s.after.md" % n))
            self.assertGreaterEqual(before["score"], 30, n)
            self.assertLess(after["score"], 10, n)
            self.assertLessEqual(after["words"], before["words"] * 1.4, n)  # rewrite does not pad

    def test_patterns_md_is_current(self):
        self.assertEqual(deslop.patterns_markdown(), read("references/patterns.md"))


class TestReadmeNumbers(unittest.TestCase):
    def test_pattern_counts_in_readmes(self):
        s = deslop.stats()
        for rel in ("README.md", "README.ru.md", "SKILL.md"):
            t = read(rel)
            self.assertIn(str(s["patterns"]), t, rel)
            self.assertIn(str(s["by_lang"]["ru"]), t, rel)
            self.assertIn(str(s["by_lang"]["en"]), t, rel)
        for rel in ("README.md", "README.ru.md"):
            t = read(rel)
            self.assertRegex(t, r"\b%d\b[^\n]*structure checks|\b%d\b[^\n]*проверок формы" % (
                s["structure_checks"], s["structure_checks"]), rel)
            self.assertIn(str(s["safe_cuts"]), t, rel)

    def test_readme_scores_match_reports(self):
        """Any README line that names examples/<name>.before.md and quotes N/100 values must match scores.txt
        (first value = before score, second = after score)."""
        scores = {}
        for line in read("examples/reports/scores.txt").split("\n"):
            m = re.match(r"(examples/\S+)\s+(\d+)/100", line)
            if m:
                scores[m.group(1)] = int(m.group(2))
        checked = 0
        for rel in ("README.md", "README.ru.md", "examples/README.md"):
            for line in read(rel).split("\n"):
                m = re.search(r"`(?:examples/)?([a-z-]+)(?:\.before\.md)?`[^\n]*?\|\s*(\d+)/100\s*\|\s*(\d+)/100", line)
                if not m:
                    continue
                name, before, after = m.group(1), int(m.group(2)), int(m.group(3))
                self.assertEqual(scores.get("examples/%s.before.md" % name), before, line)
                self.assertEqual(scores.get("examples/%s.after.md" % name), after, line)
                checked += 1
        self.assertGreaterEqual(checked, 3 * len(NAMES))

    def test_demo_transcript_is_real(self):
        """Every output line in assets/demo.txt must be a line the checker printed on an example file."""
        printed = set()
        for n in NAMES:
            for kind in ("before", "after"):
                printed.update(l.strip() for l in run(["check", "--no-fix", "examples/%s.%s.md" % (n, kind)]).split("\n"))
        for raw in read("assets/demo.txt").split("\n"):
            if not raw or raw[0] not in ">!+":
                continue
            content = re.sub(r"\{[ylbd]:([^}]*)\}", r"\1", raw[2:]).strip()
            self.assertIn(content, printed, raw)


if __name__ == "__main__":
    unittest.main()
