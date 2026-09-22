"""Freeze the four sample programs that ship under /app/progs.

The two scale samples come from the same recipes the graded families use, at a seed that is
not the one the run is graded on, so the agent can time the shapes the limit is set against
without having seen a graded program.
"""
import pathlib
import random
import sys

sys.path.insert(0, "/home/user/project-caesar/tasks/widen-pin-bind/tests")
import gen  # noqa: E402

OUT = pathlib.Path("/home/user/project-caesar/tasks/widen-pin-bind/environment/app_src/progs")


def main():
    for fam, name in (("deep", "deep.txt"), ("wide", "wide.txt")):
        rng = random.Random("sample|%s" % fam)
        lines = gen.build(fam, rng)
        text = "\n".join(lines) + "\n"
        assert "\r" not in text
        (OUT / name).write_text(text, encoding="utf-8", newline="\n")
        print("%s: %d lines, %d bytes" % (name, len(lines), len(text)))


if __name__ == "__main__":
    main()
