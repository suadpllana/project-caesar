from . import look, say, unit, watch
from .know import Know
from .line import Line


class Reader:
    def __init__(self, pg):
        self.pg = pg
        self.know = Know()
        self.line = Line()
        self.play = None

    def load(self):
        pass

    def _say(self, t, cls, text, out):
        self.play = (cls, t + len(text.split(" ")))
        out.append(say.start(t, cls, text))

    def step(self, t, recs):
        pg = self.pg
        out = []
        if self.play is not None and self.play[1] <= t:
            self.play = None
        done = set()
        for kind, r, n, text in watch.changes(pg, recs):
            if kind not in look.relevant(pg, n):
                continue
            if look.busy(pg, r):
                continue
            u = unit.unit(pg, r)
            if u is not None:
                if u in done:
                    continue
                done.add(u)
                text = unit.text_of(pg, u)
            elif kind == "removals":
                text = "removed " + text
            if not text or not self.know.fresh(r, text):
                continue
            self.know.mark(r, text)
            cls = look.loud(pg, r)
            if cls == "assertive":
                if self.play is not None and self.play[0] == "polite":
                    out.append(say.cut(t))
                    self.play = None
                self.line.flush()
                if self.play is None:
                    self._say(t, cls, text, out)
                else:
                    self.line.push(cls, text)
            else:
                self.line.push(cls, text)
        if self.play is None:
            nxt = self.line.pop()
            if nxt is not None:
                self._say(t, nxt[0], nxt[1], out)
        return out
