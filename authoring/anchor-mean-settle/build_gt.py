"""Freeze the hand cases' traces, and prove that nothing already frozen moved.

Every answer here comes from the sealed model, never from the reference, and an answer that
has been frozen once is expected to stay byte for byte identical through any later change.
When one does move, the run says which case and stops: a changed answer is a contract change
and needs saying out loud, not a rebuild of the file.

Which means the guard has to tell a changed contract from a changed program, or it cries
about every case that gets retuned. The ops of each frozen case are hashed into a file
beside this script, outside the bundle: an answer that moved while its ops stayed the same
is a contract change and stops the run, and one that moved because its own program was
rewritten is reported as a rewrite and allowed through.
"""
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "anchor-mean-settle"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases  # noqa: E402
import model  # noqa: E402

GT = TASK / "tests" / "seal" / "gt.json"
SIG = HERE / "gt_sig.json"


def sig(ops):
    return hashlib.sha256("\n".join(ops).encode("utf-8")).hexdigest()[:16]


def main():
    old = json.loads(GT.read_text(encoding="utf-8")) if GT.is_file() else {}
    was = json.loads(SIG.read_text(encoding="utf-8")) if SIG.is_file() else {}
    new = {name: model.expect(cases.ops(name)) for name in cases.ORDER}
    now = {name: sig(cases.ops(name)) for name in cases.ORDER}

    moved = [n for n in sorted(set(old) & set(new)) if old[n] != new[n]]
    rewritten = [n for n in moved if was.get(n) != now[n]]
    real = [n for n in moved if n not in rewritten]
    for n in rewritten:
        print("%s: the program itself was rewritten\n  was  %s\n  now  %s"
              % (n, " | ".join(old[n]), " | ".join(new[n])))
    if real and "--accept" not in sys.argv:
        for n in real:
            print("%s\n  was  %s\n  now  %s" % (n, " | ".join(old[n]), " | ".join(new[n])))
        raise SystemExit("%d frozen answer(s) moved on an unchanged program - that is a "
                         "contract change" % len(real))

    text = json.dumps(new, indent=1, sort_keys=True) + "\n"
    assert "\r" not in text
    with open(GT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    with open(SIG, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(now, indent=1, sort_keys=True) + "\n")
    print("%d cases frozen, %d held from before, %d new, %d retuned, %d moved on an "
          "unchanged program"
          % (len(new), len(set(old) & set(new)) - len(moved),
             len(set(new) - set(old)), len(rewritten), len(real)))


if __name__ == "__main__":
    main()
