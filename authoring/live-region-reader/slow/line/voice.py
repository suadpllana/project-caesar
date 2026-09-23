"""The reader: one tick at a time, in the order the model fixes.

At the end of every tick, after the tick's mutations: the playing utterance finishes if its time
is up, and teaches its carried values; the page is observed and every difference absorbed, aged
or held; a pending assertive difference cuts a playing polite utterance, and everything the cut
utterance carried goes back into the line at the age it had when it was taken; and whenever the
reader is free it takes the oldest pending difference, assertive before polite.

What it says is decided when it starts, never earlier. A difference inside an atomic unit makes
the whole unit speak - its exposed text as it stands now - and the utterance carries every pending
difference whose unit that is, however young, while held ones stay behind even though their text
is being read. An utterance of w words started at the end of tick t finishes at the end of tick
t + w. A unit with no exposed text says nothing: its differences are believed at once and the
reader chooses again in the same tick.
"""
from . import look, say, unit
from .know import Know
from .line import Line
from .watch import Watch


class Reader:
    def __init__(self, pg):
        self.pg = pg
        self.know = Know()
        self.line = Line()
        self.watch = Watch(pg, self.know, self.line)
        self.play = None

    def load(self):
        self.know.load(self.watch.survey())

    def _pick(self):
        return self.line.top("assertive") or self.line.top("polite")

    def _group(self, u):
        pg, know, line, watch = self.pg, self.know, self.line, self.watch
        texts, els = unit.read(pg, u)
        group = []
        for x in texts:
            r, cur = watch.now(x)
            k = (r, x)
            if line.ready(k) and unit.unit(pg, know, k, cur) == u:
                group.append((k, cur))
        for a in els:
            for k in line.anchored(a):
                if line.ready(k) and unit.unit(pg, know, k, None) == u:
                    group.append((k, None))
        return " ".join(pg.text(x) for x in texts), group

    def step(self, t, recs):
        pg, know, line, watch = self.pg, self.know, self.line, self.watch
        out = []
        if self.play is not None and self.play[1] == t:
            know.finish()
            self.play = None

        watch.scan(recs, t)

        if self.play is not None and self.play[0] == "polite" and line.top("assertive"):
            out.append(say.cut(t))
            self.play = None
            for k, (_v, age) in know.cut().items():
                watch.settle(k, t, age=age)

        while self.play is None:
            k0 = self._pick()
            if k0 is None:
                break
            r0, n0 = k0
            rr, cur = watch.now(n0)
            c0 = cur if rr == r0 else None
            u = unit.unit(pg, know, k0, c0)
            if u is not None:
                words, group = self._group(u)
            else:
                group = [(k0, c0)]
                words = c0[0] if c0 is not None else "removed " + know.expect(k0)[0]
            carried = {k: (c, line.age[k]) for k, c in group}
            for k in carried:
                line.drop(k)
            if not words:
                for k, (v, _age) in carried.items():
                    know.believe(k, v)
                continue
            cls = look.loudness(pg, r0)
            know.take(carried)
            self.play = (cls, t + len(words.split(" ")))
            out.append(say.start(t, cls, words))
        return out
