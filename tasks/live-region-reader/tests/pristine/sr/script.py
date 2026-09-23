import re


class Bad(Exception):
    pass


WORD = re.compile(r"^[a-z0-9]+$")
NAME = re.compile(r"^[a-z][a-z-]*$")


def _int(tok, what):
    try:
        v = int(tok)
    except ValueError:
        raise Bad("%s is not a number: %s" % (what, tok))
    if v < 0:
        raise Bad("%s is negative: %s" % (what, tok))
    return v


def _pos(tok):
    if tok == "end":
        return None
    return _int(tok, "position")


def _words(part, head):
    if not part:
        raise Bad("%s needs text" % head)
    for w in part:
        if not WORD.match(w):
            raise Bad("%s text has a bad word: %s" % (head, w))
    return " ".join(part)


def _op(part):
    head = part[0]
    if head == "add":
        if len(part) < 6 or part[4] not in ("el", "tx"):
            raise Bad("add takes id, parent, position, el or tx, then a tag or text")
        nid = _int(part[1], "id")
        par = _int(part[2], "parent")
        pos = _pos(part[3])
        if part[4] == "el":
            if len(part) != 6 or not NAME.match(part[5]):
                raise Bad("add el takes one tag")
            return ("add", nid, par, pos, "el", part[5])
        return ("add", nid, par, pos, "tx", _words(part[5:], "add tx"))
    if head == "move":
        if len(part) != 4:
            raise Bad("move takes id, parent, position")
        return ("move", _int(part[1], "id"), _int(part[2], "parent"), _pos(part[3]))
    if head == "drop":
        if len(part) != 2:
            raise Bad("drop takes id")
        return ("drop", _int(part[1], "id"))
    if head == "text":
        if len(part) < 3:
            raise Bad("text takes id and text")
        return ("text", _int(part[1], "id"), _words(part[2:], "text"))
    if head == "set":
        if len(part) < 4 or not NAME.match(part[2]):
            raise Bad("set takes id, name and value")
        return ("set", _int(part[1], "id"), part[2], " ".join(part[3:]))
    if head == "unset":
        if len(part) != 3 or not NAME.match(part[2]):
            raise Bad("unset takes id and name")
        return ("unset", _int(part[1], "id"), part[2])
    raise Bad("unknown op %s" % head)


def parse(text):
    last = None
    ticks = {}
    cur = None
    for raw in text.splitlines():
        part = raw.split()
        if not part:
            continue
        head = part[0]
        if head == "page":
            if last is not None or len(part) != 2:
                raise Bad("page takes one number, once")
            last = _int(part[1], "last tick")
        elif head.startswith("@"):
            if last is None:
                raise Bad("tick before page")
            t = _int(head[1:], "tick")
            if cur is not None and t <= cur:
                raise Bad("ticks must rise: %d after %d" % (t, cur))
            if cur is None and t != 0:
                raise Bad("the first tick is @0")
            if t > last:
                raise Bad("tick %d is past the last tick %d" % (t, last))
            cur = t
            ticks[t] = []
        else:
            if cur is None:
                raise Bad("op before the first tick")
            ticks[cur].append(_op(part))
    if last is None or 0 not in ticks:
        raise Bad("a page needs a page line and @0")
    return last, ticks
