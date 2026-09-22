from rs import join
from rs.idx import Idx
from rs.lex import Blank


def report(st):
    ix = {name: Idx(t) for name, t in st.tabs.items()}
    got = {q: set() for q in st.asks}
    for rl in st.rules:
        for row in join.derive(st, ix, rl):
            if not any(isinstance(v, Blank) for v in row):
                got[rl.ask].add(row)
    return got
