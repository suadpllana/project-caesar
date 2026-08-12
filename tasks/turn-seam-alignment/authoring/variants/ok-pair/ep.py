from chat import tmpl
from tok import inc


class Ep:
    def __init__(self, rt, eid, salt):
        self.rt = rt
        self.eid = eid
        self.salt = int(salt)
        self.msgs = []
        self.turns = []

    def enc(self, text):
        prev = self.rt.store.get(self.eid)
        if prev is None:
            ids = inc.encode(self.rt.tok, text, "", [])
        else:
            ids = inc.encode(self.rt.tok, text, prev[0], prev[1])
        self.rt.store.put(self.eid, text, ids)
        return ids

    def user(self, text):
        self.msgs.append(("u", text))
        self.rt.note("user", self.eid)

    def tool(self, text):
        self.msgs.append(("t", text))
        self.rt.note("tool", self.eid)

    def turn(self, cap):
        p = self.enc(tmpl.render(self.msgs, True))
        g = self.rt.gen.run(self.eid, p, self.salt, int(cap))
        self.msgs.append(("b", self.rt.tok.decode(g)))
        # The prompt goes into the record with the reply. What the trainer sees has
        # to be compared against the whole of what the sampler was conditioned on,
        # not just the part it produced, and the prompt's own last token is not
        # safe from the reply that follows it.
        self.turns.append([len(p), list(p) + list(g)])
        self.rt.note("turn", self.eid)

    def retry(self, text):
        while self.msgs and self.msgs[-1][0] != "b":
            self.msgs.pop()
        if self.msgs:
            self.msgs.pop()
            # A turn a retry threw away is not part of the episode any more, so it
            # carries no trainable positions and no record.
            self.turns.pop()
        self.msgs.append(("t", text))
        self.rt.note("retry", self.eid)

    def finish(self):
        seq = self.enc(tmpl.render(self.msgs, False))
        self.rt.done(self.eid, seq, self.turns)
        self.rt.note("done", self.eid)
