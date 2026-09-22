GRAINS = ("h", "d")
WORDS = ("now", "src", "step", "stand", "pin", "fix")


class Bad(Exception):
    pass


class Pipe:
    def __init__(self):
        self.now = None
        self.names = []
        self.pos = {}
        self.grain = {}
        self.keep = {}
        self.reads = {}
        self.roll = {}
        self.pins = set()
        self.fix = None


def _num(tok, no, what):
    try:
        val = int(tok)
    except ValueError:
        raise Bad("line %d: %s must be a whole number, got %r" % (no, what, tok))
    return val


def _read(pp, name, grain, tok, no):
    if tok.endswith("/d"):
        src = tok[:-2]
        if pp.grain.get(src) != "h" or grain != "d":
            raise Bad("line %d: %s is read by the day only from an hourly set into a daily step"
                      % (no, tok))
        return ("day", src, 0)
    if tok.endswith("-1"):
        src = tok[:-2]
        if src != name and src not in pp.grain:
            raise Bad("line %d: %s reads %s before it is declared" % (no, name, src))
        return ("prev", src, 0)
    if "~" in tok:
        src, _, width = tok.partition("~")
        width = _num(width, no, "a window")
        if width < 2:
            raise Bad("line %d: a window covers at least two partitions" % no)
    else:
        src, width = tok, 0
    if src == name or src not in pp.grain:
        raise Bad("line %d: %s reads %s before it is declared" % (no, name, src))
    if pp.grain[src] != grain:
        raise Bad("line %d: %s and %s are not of the same grain" % (no, name, src))
    return ("win", src, width) if width else ("same", src, 0)


def load(text):
    pp = Pipe()
    for no, raw in enumerate(text.splitlines(), 1):
        ws = raw.split()
        if not ws:
            continue
        op = ws[0]
        if op not in WORDS:
            raise Bad("line %d: unknown declaration %r" % (no, op))
        if op == "now":
            pp.now = _num(ws[1], no, "now")
        elif op in ("src", "step"):
            if len(ws) < 4 or (op == "step" and len(ws) < 5):
                raise Bad("line %d: %s is missing a field" % (no, op))
            name, grain = ws[1], ws[2]
            if name in pp.grain or name in WORDS:
                raise Bad("line %d: %s is declared twice" % (no, name))
            if grain not in GRAINS:
                raise Bad("line %d: grain is h or d, got %r" % (no, grain))
            keep = _num(ws[3], no, "a keep")
            if op == "step":
                pp.reads[name] = [_read(pp, name, grain, tok, no) for tok in ws[4:]]
            pp.pos[name] = len(pp.names)
            pp.names.append(name)
            pp.grain[name] = grain
            pp.keep[name] = keep
        elif op == "stand":
            roll, hourly = ws[1], ws[2]
            if pp.reads.get(roll) != [("day", hourly, 0)]:
                raise Bad("line %d: %s does not roll up %s by the day" % (no, roll, hourly))
            pp.roll[hourly] = roll
        elif op == "pin":
            if ws[1] not in pp.grain:
                raise Bad("line %d: %s is not declared" % (no, ws[1]))
            for tok in ws[2:]:
                pp.pins.add((ws[1], _num(tok, no, "a partition")))
        else:
            if ws[1] not in pp.grain or ws[1] in pp.reads:
                raise Bad("line %d: only a source partition is corrected" % no)
            pp.fix = (ws[1], _num(ws[2], no, "a partition"))
    if pp.now is None or pp.fix is None:
        raise Bad("a pipeline needs now and fix")
    return pp
