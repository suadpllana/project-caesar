"""Write authoring/variants/ok-*/ from the reference plus one declared override each.

A variant is the reference with one thing done differently, so every other file in it
is the reference by construction and is regenerated from it here; hand-copied variants
drift the moment the reference changes and the symptom is every correct implementation
failing at once.

    ok-recursive-spot    the landing chain resolved by a recursive function
    ok-record-subtree    every widget of a dropped subtree has its place recorded at the
                         drop, instead of read back off the detached parent later
    ok-eager-splice      a screen popped out of order splices its return record into the
                         screen above it at that moment, instead of being chained through
                         at the later pop
    ok-point-class       points carried as a small class rather than a tuple - the
                         invented-representation mirror
"""

import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
REF = os.path.join(TASK, "solution")
OUT = os.path.join(HERE, "variants")
POL = ("focus.py", "keep.py", "reach.py", "mem.py")


def strip(text):
    if text.startswith('"""'):
        text = text.split('"""', 2)[2].lstrip("\n")
    return text


def ref():
    return {n: strip(open(os.path.join(REF, n)).read()) for n in POL}


def swap(files, fn, old, new):
    if files[fn].count(old) != 1:
        raise SystemExit("variant anchor missing in %s: %r" % (fn, old[:50]))
    files[fn] = files[fn].replace(old, new)


def recursive_spot(files):
    swap(files, "keep.py",
         "        while tgt is not None:\n            if isinstance(tgt, Nd):\n"
         "                if reach.alive(ui, tgt):\n                    return tgt\n"
         "                tgt = self.place(tgt)\n            else:\n"
         "                if reach.alive(ui, tgt[1]):\n                    return tgt\n"
         "                tgt = self.place(tgt[1])\n        return None\n",
         "        if tgt is None:\n            return None\n"
         "        node = tgt if isinstance(tgt, Nd) else tgt[1]\n"
         "        if reach.alive(ui, node):\n            return tgt\n"
         "        return self.spot(ui, self.place(node))\n")


def record_subtree(files):
    swap(files, "keep.py",
         "        self.gone[nd] = (nd.par, at)\n",
         "        self.gone[nd] = (nd.par, at)\n\n        def walk(n):\n"
         "            for i, k in enumerate(n.kids):\n                self.gone[k] = (n, i)\n"
         "                walk(k)\n\n        walk(nd)\n")


def eager_splice(files):
    swap(files, "focus.py",
         "    def pop(self, ui, s, at):\n        if at is None or at != len(ui.st):\n"
         "            return\n",
         "    def pop(self, ui, s, at):\n        if at is None or at != len(ui.st):\n"
         "            if at is not None and at < len(ui.st):\n"
         "                above = ui.st[at]\n"
         "                self.keep.ret[above] = self.keep.ret.get(s)\n"
         "            return\n")


def point_class(files):
    swap(files, "keep.py",
         "class Keep:\n",
         "class Pt:\n    __slots__ = (\"p\", \"i\")\n\n    def __init__(self, p, i):\n"
         "        self.p = p\n        self.i = i\n\n\nclass Keep:\n")
    swap(files, "keep.py",
         "            p, at = self.gone[nd]\n            return (\"pt\", p, at)\n"
         "        return (\"pt\", nd.par, nd.par.kids.index(nd))\n",
         "            p, at = self.gone[nd]\n            return Pt(p, at)\n"
         "        return Pt(nd.par, nd.par.kids.index(nd))\n")
    swap(files, "keep.py",
         "                if reach.alive(ui, tgt[1]):\n                    return tgt\n"
         "                tgt = self.place(tgt[1])\n",
         "                if reach.alive(ui, tgt.p):\n                    return tgt\n"
         "                tgt = self.place(tgt.p)\n")
    swap(files, "focus.py",
         "from ui.keep import Keep\n", "from ui.keep import Keep, Pt\n")
    swap(files, "focus.py",
         "            self.lose(ui, (\"pt\", s.root, 0))\n",
         "            self.lose(ui, Pt(s.root, 0))\n")
    swap(files, "focus.py",
         "        elif isinstance(r, tuple) and r[1] in at:\n"
         "            # From a point: the first stop at or after it, or the last stop before it.\n"
         "            p, i = r[1], r[2]\n",
         "        elif isinstance(r, Pt) and r.p in at:\n"
         "            p, i = r.p, r.i\n")


VARIANTS = {
    "ok-recursive-spot": recursive_spot,
    "ok-record-subtree": record_subtree,
    "ok-eager-splice": eager_splice,
    "ok-point-class": point_class,
}


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    for name, fn in VARIANTS.items():
        files = ref()
        fn(files)
        d = os.path.join(OUT, name)
        os.makedirs(d)
        for n, src in files.items():
            with open(os.path.join(d, n), "w", newline="\n") as fh:
                fh.write(src)
    print("%d variants written" % len(VARIANTS))


if __name__ == "__main__":
    main()
