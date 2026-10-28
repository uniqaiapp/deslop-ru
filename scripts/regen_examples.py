#!/usr/bin/env python3
"""Regenerate every committed output that tests compare byte-for-byte.

  python3 scripts/regen_examples.py

Writes:
  examples/reports/<name>.check.txt   deslop.py check --no-fix examples/<name>.before.md
  examples/reports/<name>.audit.txt   deslop.py audit examples/<name>.before.md
  examples/reports/<name>.strip.md    deslop.py strip examples/<name>.before.md
  examples/reports/scores.txt         one line per example file: score, verdict
  references/patterns.md              deslop.py patterns --markdown

Run it after changing a pattern, then review the diff: that is the honesty check for every
number in README.md.
"""
import io
import os
import sys
from contextlib import redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import deslop  # noqa: E402


def run(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        cwd = os.getcwd()
        os.chdir(ROOT)
        try:
            deslop.main(argv)
        finally:
            os.chdir(cwd)
    return buf.getvalue()


def write(rel, content):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("wrote", rel)


def main():
    ex = os.path.join(ROOT, "examples")
    names = sorted(f[:-len(".before.md")] for f in os.listdir(ex) if f.endswith(".before.md"))
    scores = []
    for name in names:
        before = "examples/%s.before.md" % name
        write("examples/reports/%s.check.txt" % name, run(["check", "--no-fix", before]))
        write("examples/reports/%s.audit.txt" % name, run(["audit", before]))
        write("examples/reports/%s.strip.md" % name, run(["strip", before]))
    for name in names:
        for kind in ("before", "after"):
            rel = "examples/%s.%s.md" % (name, kind)
            with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
                res = deslop.analyze(f.read())
            scores.append("%-36s %3d/100  %s" % (rel, res["score"], res["verdict"]))
    write("examples/reports/scores.txt", "\n".join(scores) + "\n")
    write("references/patterns.md", deslop.patterns_markdown())
    return 0


if __name__ == "__main__":
    sys.exit(main())
