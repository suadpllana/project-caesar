"""Reference against the sealed model on generated plans.

Nothing that depends on the reference being right may be believed until this is
clean: the ground truth is written by the reference and re-proved by the model,
and the two were written from the same specification by different routes.
"""

import pathlib
import shutil
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "authoring"))
sys.path.insert(0, str(ROOT / "tests"))

import gen
import harness
import oracle


def main(argv):
    n = int(argv[1]) if len(argv) > 1 else 300
    nonce = argv[2] if len(argv) > 2 else "fuzz"
    app = harness.tree(str(ROOT / "solution"))
    bad = 0
    rows = 0
    t0 = time.time()
    try:
        for name, p in gen.batch(nonce, n):
            text = gen.text(p)
            try:
                a = harness.drive(app, text)
            except Exception as exc:
                print("REF FAULT", name, repr(exc)[:200])
                print(text)
                bad += 1
                continue
            b = oracle.play(text)
            rows += len(a["tr"])
            if a["tr"] != b["tr"] or a["sk"] != b["sk"]:
                bad += 1
                print("MISMATCH", name)
                for i, (x, y) in enumerate(zip(a["tr"], b["tr"])):
                    if x != y:
                        print("   row", i, "ref", x, "model", y)
                        break
                if len(a["tr"]) != len(b["tr"]):
                    print("   lengths", len(a["tr"]), len(b["tr"]))
                if bad > 3:
                    print(text)
                    break
    finally:
        shutil.rmtree(app.parent, ignore_errors=True)
    print("plans %d rows %d mismatches %d in %.1fs" % (n, rows, bad, time.time() - t0))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
