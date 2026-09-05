import pathlib
import shutil

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / HERE.name
SOL = TASK / "solution"
OUT = HERE / "variants"

CONTEXT = """def note(bk, tok, at):
    bk.setdefault(at, []).append(tok)


def at_of(bk, tok, st):
    for at in sorted(bk):
        if tok in bk[at]:
            return at
    return st.top()
"""

SERIAL = """def order(mine):
    return sorted(mine, key=lambda i: -i)
"""

WALKDOWN = """from wire.reg import SING
from wire.scope import ROOT
from wire import pin


def homes(tbl, st, batch, at):
    kind = dict((i, tbl[nm].life) for i, nm, up in batch)
    name = dict((i, nm) for i, nm, up in batch)
    kids = {}
    for i, nm, up in batch:
        kids.setdefault(up, []).append(i)
    out = {}
    stack = [(i, False) for i in sorted(kids.get(0, []))]
    while stack:
        i, deep = stack.pop()
        deep = deep or kind.get(i) == SING
        if deep:
            out[i] = ROOT
        else:
            tag = tbl[name[i]].tag
            out[i] = pin.where(st, at, tag) if tag else at
        for c in sorted(kids.get(i, [])):
            stack.append((c, deep))
    for i in kind:
        out.setdefault(i, at)
    return out
"""

FORWARD = """from wire.scope import ROOT


def where(st, at, tag):
    found = ROOT
    for sc in st.upto(at):
        if st.tag(sc) == tag:
            found = sc
    return found
"""

OVERRIDES = {
    "ok-context": ("hold.py", CONTEXT),
    "ok-serial": ("tear.py", SERIAL),
    "ok-walkdown": ("own.py", WALKDOWN),
    "ok-forward-scan": ("pin.py", FORWARD),
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
