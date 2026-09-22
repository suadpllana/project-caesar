"""The sealed model: what every reference of a program denotes, derived straight from the rules.

Written apart from the reference solution, and deliberately organised differently from it: it
parses the program itself, keeps a candidate's visibility as the path of the module whose
subtree can see it (None for every module) rather than as a depth, keeps one exact set per such
root rather than cumulative sets, solves by whole rounds over every module rather than by a
worklist, and allocates a binding's bit only when that binding first appears.

THE RULES, as the instruction states them, and where each is applied below:

  presence       a line ending `if F` exists only while flag F is on, `if !F` only while it is
                 off; an absent line neither binds nor gives                    -> _present
  visibility     a `pub` line is seen from every module; any other line from its own module
                 and every module inside it (a module is inside every module whose path is a
                 dot-prefix of its own)                                         -> _sees
  explicit       `use P::N as K` gives, under K, each candidate P has under N that the importing
                 module can see, seen from where both the candidate and the line
                 are seen                                                       -> _through
  glob           `use P::*` does the same under every name the module does not
                 bind itself                                                    -> _round
  hiding         a module binds a name itself when it has a present item or explicit import
                 line for it; it then has under that name exactly what those lines give, even
                 nothing, and its globs give it nothing under that name       -> _round (mask)
  routes         a candidate reached by several chains counts once, seen from every module any
                 chain allows                                                   -> _merge
  fixed point    a candidate is had only through a chain of lines ending at its item line; a
                 cycle alone gives nothing                               -> start empty, rounds
  outcome        one candidate prints module.name; none prints `broken` when the referencing
                 module binds the name itself and `unresolved` otherwise; more print
                 `ambiguous` and every candidate in the order of its item line  -> expect
"""


def _parse(lines):
    """Program text -> (flags on, module order, per-module line tuples, items, refs)."""
    on = None
    order, mods, items, refs = [], {}, [], []
    cur = None
    for raw in lines:
        t = raw.split()
        if not t:
            continue
        if on is None:
            assert t[0] == "flags", raw
            on = set(t[1:])
            continue
        if t[0] == "mod":
            cur = t[1]
            order.append(cur)
            mods[cur] = []
            continue
        if t[0] == "ref":
            refs.append((cur, t[1]))
            continue
        pub = t[0] == "pub"
        if pub:
            t = t[1:]
        cond = None
        if len(t) >= 2 and t[-2] == "if":
            f = t[-1]
            cond = (f[1:], False) if f.startswith("!") else (f, True)
            t = t[:-2]
        if t[0] == "item":
            mods[cur].append(("item", t[1], pub, cond, len(items)))
            items.append((cur, t[1]))
        else:
            src, _, name = t[1].rpartition("::")
            if name == "*":
                mods[cur].append(("glob", src, pub, cond))
            else:
                bound = t[3] if len(t) == 4 else name
                mods[cur].append(("use", src, name, bound, pub, cond))
    return on, order, mods, items, refs


def _present(cond, on):
    return cond is None or (cond[0] in on) == cond[1]


def _inside(a, b):
    """True when module a is b or lies inside b."""
    return a == b or a.startswith(b + ".")


def _sees(root, reader):
    """Can `reader` see a candidate whose visibility root is `root` (None: every module)?"""
    return root is None or _inside(reader, root)


def _narrower(r1, r2):
    """The intersection of two visibility roots that both contain the reader.

    Both are None or an ancestor-or-self path of the same module, so one contains the other and
    the intersection is simply the deeper of the two.
    """
    if r1 is None:
        return r2
    if r2 is None:
        return r1
    return r1 if len(r1) >= len(r2) else r2


class _Bits:
    """Bindings - (item, name under which it is held) - allocated as they first appear."""

    def __init__(self, items):
        self.id = {}
        self.of = []
        self.name_mask = {}
        self.by_name = {}
        for ix, (_m, name) in enumerate(items):
            self.get(ix, name)

    def get(self, ix, name):
        b = self.id.get((ix, name))
        if b is None:
            b = len(self.of)
            self.id[(ix, name)] = b
            self.of.append((ix, name))
            self.name_mask[name] = self.name_mask.get(name, 0) | (1 << b)
            self.by_name.setdefault(name, []).append(ix)
        return b

    def rename(self, x, name, bound):
        """Bits of x held under `name` -> the same items held under `bound`."""
        y = 0
        for ix in list(self.by_name.get(name, ())):
            b = self.id[(ix, name)]
            if x >> b & 1:
                y |= 1 << self.get(ix, bound)
        return y


def _merge(into, root, bits):
    """Add `bits` at visibility root `root`, keeping each binding only at its widest root."""
    if bits:
        into[root] = into.get(root, 0) | bits


def _normalise(held):
    """Drop every binding from any root narrower than another root that also holds it."""
    out = {}
    wider = 0
    for root in sorted(held, key=lambda r: -1 if r is None else len(r)):
        b = held[root] & ~wider
        if b:
            out[root] = b
            wider |= b
    return out


def _through(src_held, reader, line_root):
    """What a line of `reader` receives from a source's holdings, root by root."""
    got = {}
    for root, bits in src_held.items():
        if _sees(root, reader):
            _merge(got, _narrower(root, line_root), bits)
    return got


def expect(lines):
    on, order, mods, items, refs = _parse(lines)
    bits = _Bits(items)

    # Present lines and the names each module binds itself (decided by lines alone).
    own_items, own_uses, globs, binds = {}, {}, {}, {}
    for m in order:
        oi, ou, gl, bn = [], [], [], set()
        for ln in mods[m]:
            kind = ln[0]
            if kind == "item" and _present(ln[3], on):
                oi.append((ln[4], ln[1], None if ln[2] else m))
                bn.add(ln[1])
            elif kind == "use" and _present(ln[5], on):
                ou.append((ln[1], ln[2], ln[3], None if ln[4] else m))
                bn.add(ln[3])
            elif kind == "glob" and _present(ln[3], on):
                gl.append((ln[1], None if ln[2] else m))
        own_items[m], own_uses[m], globs[m], binds[m] = oi, ou, gl, bn

    def mask_of(names):
        mk = 0
        for n in names:
            mk |= bits.name_mask.get(n, 0)
        return mk

    # Least fixed point by whole rounds: every module is re-derived from the previous round's
    # holdings, starting from nothing, until a round changes nothing.
    held = {m: {} for m in order}
    while True:
        nxt = {}
        for m in order:
            got = {}
            for ix, name, root in own_items[m]:
                _merge(got, root, 1 << bits.get(ix, name))
            for src, name, bound, root in own_uses[m]:
                if src not in held:
                    continue
                for r, b in _through(held[src], m, root).items():
                    x = b & bits.name_mask.get(name, 0)
                    if x and bound != name:
                        x = bits.rename(x, name, bound)
                    _merge(got, r, x)
            keep = ~mask_of(binds[m])
            for src, root in globs[m]:
                if src not in held:
                    continue
                for r, b in _through(held[src], m, root).items():
                    _merge(got, r, b & keep)
            nxt[m] = _normalise(got)
        if nxt == held:
            break
        held = nxt

    out = []
    for m, name in refs:
        allb = 0
        for b in held[m].values():
            allb |= b
        allb &= bits.name_mask.get(name, 0)
        cands = sorted(ix for ix in bits.by_name.get(name, ()) if allb >> bits.id[(ix, name)] & 1)
        if len(cands) == 1:
            out.append("%s %s %s.%s" % (m, name, items[cands[0]][0], items[cands[0]][1]))
        elif not cands:
            out.append("%s %s %s" % (m, name, "broken" if name in binds[m] else "unresolved"))
        else:
            out.append("%s %s ambiguous %s" % (
                m, name, " ".join("%s.%s" % items[ix] for ix in cands)))
    return out
