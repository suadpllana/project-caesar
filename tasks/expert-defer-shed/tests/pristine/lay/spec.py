class Bad(Exception):
    pass


class Cfg:
    __slots__ = ("ex", "bw", "w", "f", "g")

    def __init__(self, ex, bw, w, f, g):
        self.ex = ex
        self.bw = bw
        self.w = w
        self.f = f
        self.g = g

    def banks(self):
        return self.ex // self.bw


def _ints(part, want, head):
    if len(part) != want:
        raise Bad("%s takes %d numbers, got %d" % (head, want, len(part)))
    try:
        return [int(x) for x in part]
    except ValueError:
        raise Bad("%s takes numbers" % head)


def parse(text):
    cfg = None
    steps = []
    for raw in text.splitlines():
        part = raw.split()
        if not part:
            continue
        head = part[0]
        if head == "cfg":
            if cfg is not None:
                raise Bad("cfg given twice")
            ex, bw, w, f, g = _ints(part[1:], 5, "cfg")
            if ex < 2 or bw < 1 or ex % bw:
                raise Bad("cfg needs at least two experts in banks that divide them")
            if w < 1 or f < 1 or g < 1 or g > 100:
                raise Bad("cfg needs a positive threshold, factor and budget share")
            cfg = Cfg(ex, bw, w, f, g)
        elif head == "step":
            if cfg is None:
                raise Bad("step before cfg")
            steps.append([])
        elif head == "mb":
            if not steps:
                raise Bad("mb before step")
            steps[-1].append([])
        elif head == "t":
            if not steps or not steps[-1]:
                raise Bad("t before mb")
            weight = tuple(_ints(part[1:], cfg.ex, "t"))
            steps[-1][-1].append(weight)
        else:
            raise Bad("unknown op %s" % head)
    if cfg is None:
        raise Bad("no cfg")
    for mbs in steps:
        if not mbs:
            raise Bad("step with no mb")
    return cfg, steps
