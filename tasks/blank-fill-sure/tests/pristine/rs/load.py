from rs import dom, lex, rule


class Tab:
    __slots__ = ("name", "cols", "rows")

    def __init__(self, name, cols):
        self.name = name
        self.cols = cols
        self.rows = []


class Store:
    __slots__ = ("tabs", "rules", "asks", "blanks")

    def __init__(self):
        self.tabs = {}
        self.rules = []
        self.asks = []
        self.blanks = {}


def read(text):
    st = Store()
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        kind, _, rest = line.partition(" ")
        try:
            if kind == "table":
                parts = rest.split()
                if len(parts) < 2 or not lex.SYM.match(parts[0]) or parts[0] in st.tabs:
                    raise ValueError("bad table")
                st.tabs[parts[0]] = Tab(parts[0], [dom.parse(p) for p in parts[1:]])
            elif kind == "row":
                parts = rest.split()
                tab = st.tabs[parts[0]]
                vals = tuple(lex.value(p, st.blanks) for p in parts[1:])
                if len(vals) != len(tab.cols):
                    raise ValueError("wrong arity")
                for c, v in zip(tab.cols, vals):
                    if not isinstance(v, lex.Blank) and not c.has(v):
                        raise ValueError("value not allowed: %r" % (v,))
                tab.rows.append(vals)
            elif kind == "rule":
                r = rule.parse(rest, st.tabs)
                st.rules.append(r)
                if r.ask not in st.asks:
                    st.asks.append(r.ask)
            else:
                raise ValueError("unknown line")
        except (ValueError, KeyError) as exc:
            raise ValueError("line %d: %s" % (n, exc)) from None
    return st
