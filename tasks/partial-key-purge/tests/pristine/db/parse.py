import re

NAME = re.compile(r"[a-z][a-z0-9_]*\Z")
VALUE = re.compile(r"[A-Za-z0-9_]+\Z")
ID = re.compile(r"[1-9][0-9]*\Z")
MODES = ("simple", "full", "partial")
ACTS = ("cascade", "restrict", "noaction", "setnull")


class Tab:
    def __init__(self, name, cols, pos):
        self.name = name
        self.cols = cols
        self.pos = pos
        self.keys = []
        self.refs = []
        self.used = []


class Key:
    def __init__(self, name, tab, cols, pos):
        self.name = name
        self.tab = tab
        self.cols = cols
        self.pos = pos


class Ref:
    def __init__(self, name, tab, cols, key, mode, act, wipe, pos):
        self.name = name
        self.tab = tab
        self.cols = cols
        self.key = key
        self.mode = mode
        self.act = act
        self.wipe = wipe
        self.pos = pos


class Stmt:
    def __init__(self, op, tab, ids):
        self.op = op
        self.tab = tab
        self.ids = ids


class Script:
    def __init__(self):
        self.tabs = []
        self.decls = []
        self.names = {}
        self.rows = []
        self.stmts = []


class Bad(Exception):
    pass


def _name(word, no):
    if not NAME.match(word):
        raise Bad("line %d: bad name %r" % (no, word))
    return word


def _cols(tab, words, no):
    out = []
    for w in words:
        if w not in tab.cols:
            raise Bad("line %d: %s has no column %r" % (no, tab.name, w))
        i = tab.cols.index(w)
        if i in out:
            raise Bad("line %d: column %r twice" % (no, w))
        out.append(i)
    if not out:
        raise Bad("line %d: no columns" % no)
    return out


def _get(sc, word, kind, no):
    got = sc.names.get(word)
    if not isinstance(got, kind):
        raise Bad("line %d: %r is not a %s" % (no, word, kind.__name__.lower()))
    return got


def _fresh(sc, word, no):
    _name(word, no)
    if word in sc.names:
        raise Bad("line %d: %r declared twice" % (no, word))
    return word


def _id(word, no):
    if not ID.match(word):
        raise Bad("line %d: bad id %r" % (no, word))
    return int(word)


def read(path):
    with open(path, encoding="utf-8") as f:
        return parse(f.read())


def parse(text):
    sc = Script()
    stage = 0
    seen = {}
    for no, raw in enumerate(text.split("\n"), 1):
        w = raw.split()
        if not w or w[0].startswith("#"):
            continue
        op = w[0]
        if op in ("table", "key", "ref"):
            if stage > 0:
                raise Bad("line %d: declaration after rows" % no)
            if op == "table":
                if len(w) < 3:
                    raise Bad("line %d: table needs columns" % no)
                name = _fresh(sc, w[1], no)
                cols = [_name(c, no) for c in w[2:]]
                if len(set(cols)) != len(cols):
                    raise Bad("line %d: repeated column" % no)
                t = Tab(name, cols, len(sc.tabs))
                sc.tabs.append(t)
                sc.names[name] = t
                seen[name] = set()
            elif op == "key":
                if len(w) < 4:
                    raise Bad("line %d: key needs columns" % no)
                name = _fresh(sc, w[1], no)
                t = _get(sc, w[2], Tab, no)
                k = Key(name, t, _cols(t, w[3:], no), len(sc.decls))
                t.keys.append(k)
                sc.decls.append(k)
                sc.names[name] = k
            else:
                if "->" not in w or len(w) < 8:
                    raise Bad("line %d: malformed ref" % no)
                arrow = w.index("->")
                name = _fresh(sc, w[1], no)
                t = _get(sc, w[2], Tab, no)
                cols = _cols(t, w[3:arrow], no)
                if len(w) < arrow + 4:
                    raise Bad("line %d: malformed ref" % no)
                k = _get(sc, w[arrow + 1], Key, no)
                mode, act = w[arrow + 2], w[arrow + 3]
                if mode not in MODES or act not in ACTS:
                    raise Bad("line %d: bad mode or action" % no)
                if len(cols) != len(k.cols):
                    raise Bad("line %d: %s has %d columns" % (no, k.name, len(k.cols)))
                rest = w[arrow + 4:]
                if rest and act != "setnull":
                    raise Bad("line %d: only setnull lists columns" % no)
                wipe = list(cols)
                if rest:
                    wipe = _cols(t, rest, no)
                    if any(i not in cols for i in wipe):
                        raise Bad("line %d: cleared column outside the ref" % no)
                if act != "setnull":
                    wipe = []
                r = Ref(name, t, cols, k, mode, act, wipe, len(sc.decls))
                t.refs.append(r)
                k.tab.used.append(r)
                sc.decls.append(r)
                sc.names[name] = r
        elif op == "row":
            if stage > 1:
                raise Bad("line %d: row after statements" % no)
            stage = 1
            if len(w) < 3:
                raise Bad("line %d: malformed row" % no)
            t = _get(sc, w[1], Tab, no)
            rid = _id(w[2], no)
            vals = w[3:]
            if len(vals) != len(t.cols):
                raise Bad("line %d: %s has %d columns" % (no, t.name, len(t.cols)))
            if rid in seen[t.name]:
                raise Bad("line %d: id %d twice" % (no, rid))
            seen[t.name].add(rid)
            out = []
            for v in vals:
                if v == "-":
                    out.append(None)
                elif VALUE.match(v):
                    out.append(v)
                else:
                    raise Bad("line %d: bad value %r" % (no, v))
            sc.rows.append((t, rid, out))
        elif op in ("delete", "dump", "audit"):
            stage = 2
            if op == "audit":
                if len(w) != 1:
                    raise Bad("line %d: audit takes nothing" % no)
                sc.stmts.append(Stmt(op, None, []))
            elif op == "dump":
                if len(w) != 2:
                    raise Bad("line %d: dump takes a table" % no)
                sc.stmts.append(Stmt(op, _get(sc, w[1], Tab, no), []))
            else:
                if len(w) < 3:
                    raise Bad("line %d: delete needs ids" % no)
                t = _get(sc, w[1], Tab, no)
                ids = [_id(x, no) for x in w[2:]]
                if len(set(ids)) != len(ids):
                    raise Bad("line %d: id named twice" % no)
                sc.stmts.append(Stmt(op, t, ids))
        else:
            raise Bad("line %d: unknown %r" % (no, op))
    return sc
