"""Generate the mirror variant, and check the independent ones are actually independent.

The mirror is the reference with every internal identifier renamed, produced mechanically so it
cannot drift: if the verifier grades a name rather than behaviour, the mirror fails and says so.
`worklist.py` and `rounds.py` are written by hand against the contract, not derived, so this
only asserts they share little text with the reference - a variant that is the reference with
whitespace moved proves nothing about implementation neutrality.

The rename is asserted to have actually fired. An earlier version of this file silently matched
nothing and wrote out the reference unchanged, which made the mirror prove nothing at all.

    python authoring/reach-pair-sweep/make_variants.py
"""
import difflib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "reach-pair-sweep"
OUT = ROOT / "authoring" / "reach-pair-sweep" / "variants"

# Locals and helpers only. Never an attribute of the heap: those are the runtime's API and a
# collector that renamed them would not run. `add` is deliberately absent - it collides with
# set.add, and renaming that produced a mirror that could not execute.
RENAME = {
    "_reach": "gather", "_close": "settle", "got": "seen", "st": "pending",
    "seed": "start", "blocked": "barred", "live": "standing",
    "hold": "reprieved", "qd": "due", "cl": "wiped", "rl": "freed", "rt": "anchors",
}

HAND = ("worklist.py", "rounds.py")


def mirror():
    src = (TASK / "solution" / "keep.py").read_text(encoding="utf-8")
    src = re.sub(r'^"""[\s\S]*?"""\n+', "", src, count=1)
    fired = 0
    for old, new in sorted(RENAME.items(), key=lambda kv: -len(kv[0])):
        src, n = re.subn(r"(?<![.\w])" + re.escape(old) + r"\b", new, src)
        if n == 0:
            raise SystemExit("rename %r matched nothing - the reference moved" % old)
        fired += n
    left = [n for n in RENAME if re.search(r"(?<![.\w])" + re.escape(n) + r"\b", src)]
    if left:
        raise SystemExit("mirror still carries reference names: %s" % left)
    (OUT / "mirror.py").write_text(src, encoding="utf-8")
    return src, fired


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ref = (TASK / "solution" / "keep.py").read_text(encoding="utf-8")
    body, fired = mirror()
    print("mirror.py written: %d lines, %d identifier substitutions made"
          % (len(body.splitlines()), fired))

    bad = 0
    for name in HAND:
        p = OUT / name
        if not p.is_file():
            print("MISSING %s" % name)
            bad += 1
            continue
        r = difflib.SequenceMatcher(None, ref, p.read_text(encoding="utf-8")).ratio()
        tag = "independent" if r < 0.55 else "TOO CLOSE to the reference"
        print("%-14s similarity to reference %.3f  %s" % (name, r, tag))
        if r >= 0.55:
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
