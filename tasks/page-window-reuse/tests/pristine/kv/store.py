from collections import deque


class Pg:
    __slots__ = ("prev", "tokens", "n")

    def __init__(self, prev, w):
        self.prev = prev
        self.tokens = [0] * w
        self.n = 0


class Rq:
    __slots__ = ("name", "seq", "prompt", "out", "fed", "made", "pg", "got", "up")

    def __init__(self, name, seq, prompt, out):
        self.name = name
        self.seq = seq
        self.prompt = prompt
        self.out = out
        self.fed = 0
        self.made = 0
        self.pg = {}
        self.got = False
        self.up = -1

    def len(self):
        return self.fed + self.made


class Kv:
    def __init__(self):
        self.n = 0
        self.w = 1
        self.a = 0
        self.s = 0
        self.b = 0
        self.pg = {}
        self.rq = {}
        self.wait = deque()
        self.on = []
        self.out = []
        self.t = 0

    def tick(self):
        self.t += 1
        return self.t

    def say(self, *part):
        self.out.append(" ".join(str(p) for p in part))
