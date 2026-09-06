class Req(object):
    __slots__ = ("rid", "idx", "at", "toks", "plen", "have", "live", "seen", "gone")

    def __init__(self, rid, idx, at):
        self.rid = rid
        self.idx = idx
        self.at = at
        self.toks = []
        self.plen = 0
        self.have = 0
        self.live = False
        self.seen = False
        self.gone = False


class Job(object):
    __slots__ = ("cap", "span", "budget", "reqs")

    def __init__(self):
        self.cap = 0
        self.span = 0
        self.budget = 0
        self.reqs = []


def parse(text):
    job = Job()
    by = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        bits = line.split()
        head = bits[0]
        if head == "pool":
            job.cap = int(bits[1])
        elif head == "block":
            job.span = int(bits[1])
        elif head == "batch":
            job.budget = int(bits[1])
        elif head == "req":
            r = Req(bits[1], len(job.reqs), int(bits[2]))
            by[bits[1]] = r
            job.reqs.append(r)
        elif head == "prompt":
            r = by[bits[1]]
            r.toks.extend(int(x) for x in bits[2:])
            r.plen = len(r.toks)
        elif head == "emit":
            r = by[bits[1]]
            r.toks.extend(int(x) for x in bits[2:])
    return job
