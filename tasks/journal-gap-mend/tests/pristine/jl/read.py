from collections import namedtuple

Entry = namedtuple("Entry", "kind lock sess out")
Dig = namedtuple("Dig", "grants mark")
Aud = namedtuple("Aud", "grants asks rels beats mark")
Gap = namedtuple("Gap", "marks")
Journal = namedtuple("Journal", "locks sessions period items")

OUTS = {"acq": ("grant", "again", "wait"), "rel": ("keep", "free", "pass")}


def _num(word, top=None):
    if not word.isdigit() or (top is not None and int(word) >= top):
        raise ValueError("bad number %r" % word)
    return int(word)


def _mark(word):
    if len(word) != 12 or any(c not in "0123456789abcdef" for c in word):
        raise ValueError("bad mark %r" % word)
    return word


def _rec(words, locks, sessions):
    head = words[0]
    if head in OUTS and len(words) == 4 and words[3] in OUTS[head]:
        return Entry(head, _num(words[1], locks), _num(words[2], sessions), words[3])
    if head == "beat" and len(words) == 2:
        return Entry("beat", None, _num(words[1], sessions), None)
    if head == "dig" and len(words) == 3:
        return Dig(_num(words[1]), _mark(words[2]))
    if head == "aud" and len(words) == 6:
        g, a, r, b = (_num(w) for w in words[1:5])
        return Aud(g, a, r, b, _mark(words[5]))
    raise ValueError("bad line %r" % " ".join(words))


def parse(text):
    rows = [ln.split() for ln in text.splitlines() if ln.strip()]
    if not rows or rows[0][0] != "cfg" or len(rows[0]) != 4:
        raise ValueError("no cfg line")
    locks, sessions, period = (_num(w) for w in rows[0][1:])
    if not 1 <= locks <= 10 or not 1 <= sessions <= 10 or period < 1:
        raise ValueError("bad cfg line")
    items = []
    marks = None
    for words in rows[1:]:
        if words == ["gap"]:
            if marks is not None:
                raise ValueError("gap inside gap")
            marks = []
        elif words == ["back"]:
            if marks is None:
                raise ValueError("back without gap")
            items.append(Gap(tuple(marks)))
            marks = None
        else:
            rec = _rec(words, locks, sessions)
            if marks is None:
                items.append(rec)
            elif isinstance(rec, Entry):
                raise ValueError("entry inside gap")
            else:
                marks.append(rec)
    if marks is not None:
        raise ValueError("gap not closed")
    return Journal(locks, sessions, period, tuple(items))
