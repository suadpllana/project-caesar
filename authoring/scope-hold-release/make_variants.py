import pathlib
import shutil

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / HERE.name
SOL = TASK / "solution"
OUT = HERE / "variants"

OVERRIDES = {
    "ok-context": ("hold.py", '''def note(bk, tok, at):
    bk.setdefault(at, []).append(tok)


def at_of(bk, tok, st):
    for at in sorted(bk):
        if tok in bk[at]:
            return at
    return st.top()
'''),
    "ok-serial": ("tear.py", '''def order(mine):
    return sorted(mine, key=lambda i: -i)
'''),
    "ok-walkdown": ("own.py", '''from wire.reg import SING
from wire.scope import ROOT


def homes(tbl, batch, at):
    kind = dict((i, tbl[nm].life) for i, nm, up in batch)
    kids = {}
    for i, nm, up in batch:
        kids.setdefault(up, []).append(i)
    out = {}
    stack = [(i, False) for i in sorted(kids.get(0, []))]
    while stack:
        i, deep = stack.pop()
        deep = deep or kind.get(i) == SING
        out[i] = ROOT if deep else at
        for c in sorted(kids.get(i, [])):
            stack.append((c, deep))
    for i in kind:
        out.setdefault(i, at)
    return out
'''),
}


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    for name, (target, body) in sorted(OVERRIDES.items()):
        d = OUT / name
        d.mkdir(parents=True)
        for f in sorted(SOL.glob("*.py")):
            shutil.copy(f, d / f.name)
        (d / target).write_text(body, newline="\n")
        (d / "README").write_text(
            "%s: the reference with %s replaced by an equivalent reading.\n" % (name, target),
            newline="\n")
    print("wrote", len(OVERRIDES), "variants")


if __name__ == "__main__":
    main()
