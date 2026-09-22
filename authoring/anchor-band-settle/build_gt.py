#!/usr/bin/env python3
"""Freeze tests/seal/gt.json: the lines every enumerated program must print.

An answer is frozen only when the sealed model and the plain full-relayout oracle both produce
it. When gt.json already exists, every answer already in it must come out byte-identical,
because the enumerated set is only ever extended, never re-derived: an answer that moves is a
contract change and is reported as one instead of being written.

    python3 build_gt.py [--allow-change NAME ...]
"""
import json
import sys

import lab

GT = lab.TASK / "tests" / "seal" / "gt.json"


def main(argv):
    allow = set(argv[argv.index("--allow-change") + 1:]) if "--allow-change" in argv else set()
    cases, _gen, model = lab.sealed()
    naive = lab.naive()
    old = json.loads(GT.read_text(encoding="utf-8")) if GT.is_file() else {}
    new, bad = {}, []
    for name in cases.ORDER:
        lines = cases.prog(name)
        want = model.expect(lines)
        also = naive.run("\n".join(lines) + "\n")
        if want != also:
            bad.append("%s: model and oracle disagree" % name)
            continue
        if name in old and old[name] != want and name not in allow:
            bad.append("%s: frozen answer moved (%s -> %s)" % (name, old[name], want))
            continue
        new[name] = want
    for name in sorted(set(old) - set(cases.ORDER)):
        bad.append("%s: frozen but no longer enumerated" % name)
    if bad:
        print("\n".join(bad))
        return 1
    text = json.dumps(new, indent=1, sort_keys=True) + "\n"
    assert "\r" not in text
    GT.write_text(text, encoding="utf-8", newline="\n")
    kept = sum(1 for n in new if n in old)
    print("gt.json: %d answers (%d kept byte-identical, %d new)" % (len(new), kept, len(new) - kept))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
