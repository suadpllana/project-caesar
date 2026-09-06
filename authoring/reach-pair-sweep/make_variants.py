"""Generate the mirror variant, and check the independent one is actually independent.

The mirror is the reference with every internal identifier renamed across all five modules,
produced mechanically so it cannot drift: if the verifier grades a name rather than behaviour,
the mirror fails and says so. The rename is asserted to have fired, because an earlier version
of this file silently matched nothing and wrote out the reference unchanged.

`alt/` is written by hand against the contract, not derived, so this only asserts it shares
little text with the reference - a variant that is the reference with whitespace moved proves
nothing about implementation neutrality.

    python authoring/reach-pair-sweep/make_variants.py
"""
import difflib
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "reach-pair-sweep"
OUT = ROOT / "authoring" / "reach-pair-sweep" / "variants"

PARTS = ("plan.py", "scan.py", "keep.py", "age.py", "wipe.py")
HAND = ("alt",)

# Locals and helpers only, never an attribute of the heap: those are the runtime's API and a
# collector that renamed them would not run.
RENAME = {
    "_settle": "walk", "_scope": "inscope",
    "by": "idx", "seen": "found", "stack": "todo", "start": "bases", "barred": "skip",
    "named": "listed", "moved": "shifted", "fresh": "newly", "held": "spared",
    "src": "owner", "fld": "slotname", "was": "recorded", "tgt": "referent",
    "scope": "inrange", "val": "now",
}

DOC = re.compile(r'^"""[\s\S]*?"""\n+')


def mirror():
    out = OUT / "mirror"
    out.mkdir(parents=True, exist_ok=True)
    fired = 0
    for part in PARTS:
        src = DOC.sub("", (TASK / "solution" / part).read_text(encoding="utf-8"), count=1)
        for old, new in sorted(RENAME.items(), key=lambda kv: -len(kv[0])):
            src, n = re.subn(r"(?<![.\w])" + re.escape(old) + r"\b", new, src)
            fired += n
        (out / part).write_text(src, encoding="utf-8", newline="\n")
    if fired == 0:
        raise SystemExit("rename matched nothing - the reference moved")
    return fired


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fired = mirror()
    print("mirror/ written: %d identifier substitutions across %d modules" % (fired, len(PARTS)))

    ref = "".join((TASK / "solution" / p).read_text(encoding="utf-8") for p in PARTS)
    bad = 0
    for name in HAND:
        d = OUT / name
        if not d.is_dir():
            print("MISSING %s" % name)
            bad += 1
            continue
        got = "".join((d / p).read_text(encoding="utf-8") for p in PARTS)
        r = difflib.SequenceMatcher(None, ref, got).ratio()
        tag = "independent" if r < 0.60 else "TOO CLOSE to the reference"
        print("%-10s similarity to reference %.3f  %s" % (name, r, tag))
        if r >= 0.60:
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
