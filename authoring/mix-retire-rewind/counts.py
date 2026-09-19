"""Every count the shipped prose states, re-derived from the code that produces it.

Counts drift with the generator, so the brief and the metadata quote these numbers rather than
remembered ones. Run it after any change to gen.py, cases.py or the harness value in test.sh.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "mix-retire-rewind"
sys.path.insert(0, str(TASK / "tests"))

import cases  # noqa: E402
import gen  # noqa: E402


def main():
    text = (TASK / "tests" / "test.sh").read_text(encoding="utf-8")
    per = int(re.search(r"^per=(\d+)$", text, re.M).group(1))
    wall = int(re.search(r"^wall=(\d+)$", text, re.M).group(1))
    work = gen.programs("counts", per)
    big = [n for fam, n, _l in work if fam in ("wide", "deep")]
    print("harness:            per=%d wall=%ds" % (per, wall))
    print("enumerated plans:   %d" % len(cases.ORDER))
    print("nonce plans:        %d (%d families)" % (len(work), len(gen.FAMILIES)))
    print("   of those big:    %d (%s)" % (len(big), ", ".join(sorted(set(
        n.split("-")[0] for n in big)))))
    print("graded plans:       %d" % (len(cases.ORDER) + len(work)))
    print("   small:           %d" % (len(cases.ORDER) + len(work) - len(big)))

    wide = (TASK / "environment" / "app_src" / "plans" / "wide.txt").read_text(encoding="utf-8")
    deep = (TASK / "environment" / "app_src" / "plans" / "deep.txt").read_text(encoding="utf-8")
    for name, body in (("wide.txt", wide), ("deep.txt", deep)):
        steps = int(re.search(r"^take r (\d+)$", body, re.M).group(1))
        geo = re.search(r"^open r (\d+) (\d+) (\d+)$", body, re.M).groups()
        span = int(geo[0]) * int(geo[1]) * int(geo[2])
        srcs = re.findall(r"^src (\S+) (\d+) (\S+)$", body, re.M)
        print("%s:           %d steps of %d slots = %d slots, %d sources of %d samples, "
              "allowances %s" % (name, steps, span, steps * span, len(srcs),
                                 len(srcs[0][2].split(",")),
                                 [int(s[1]) for s in srcs]))
    scale = [ls for fam, _n, ls in gen.programs("counts", per) if fam == "wide"][0]
    steps = int(re.search(r"take r (\d+)", "\n".join(scale)).group(1))
    print("generated wide:     %d steps in this sample" % steps)
    return 0


if __name__ == "__main__":
    sys.exit(main())
