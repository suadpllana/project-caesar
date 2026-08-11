from model.arch import M, tag


class Seq:
    def __init__(self, rid, prompt, adapter, max_new):
        self.rid = rid
        self.prompt = list(prompt)
        self.adapter = adapter
        self.max_new = max_new
        self.gen = []
        self.blocks = []
        self.keys = []
        self.filled = 0
        self.step = 0
        self.fp = None
        self.started = False
        self.done = False
        self.sync_n = 0
        self.salt = tag(rid, 7717) % M

    def toks(self):
        return self.prompt + self.gen

    def reset_cache(self):
        self.blocks = []
        self.keys = []
        self.filled = 0
