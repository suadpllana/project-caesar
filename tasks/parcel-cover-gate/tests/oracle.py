"""A second reading of the same rules, written to share no code with the tree.

Nothing here imports the machine. It parses a feed itself, keeps the history in
parallel lists rather than objects, and answers "does this version stand after
that one" out of a memoised ancestor set instead of walking the graph per
question. The pass is a queue that is refilled while it makes progress rather
than a loop over a bag. Two implementations reaching the same rows on tens of
thousands of random feeds is the only evidence anybody has that the rows in
`gt.json` are the rules and not one author's habits, so `authoring/fuzz.py`
refuses to let a ground truth be written without a clean run of exactly that.

The rules, restated from the requirements rather than from the reference:

  Standing after      version j stands after version i when i is j or i is in
                      the set reached by following what j was built on. A write
                      was built on one version, a settling on two, and the second
                      of those is only reachable through the second link.

  Covered             the picture a version's writer was showing is covered by a
                      worker when, for each setting in it, the worker shows - or
                      the parcel under test carries - a version standing after
                      the one named.

  Up                  a parcel goes up whole. Every entry has to be one the
                      worker is already at or after, or one standing after what
                      the worker shows (or a setting it has never heard of) whose
                      writer's picture is covered.

  Kept                a parcel that cannot go up stays. Anything reaching a
                      worker later, and any settling the worker does, is another
                      chance for it, and one parcel going up is itself such a
                      chance for the next.

  First               where more than one could go up, the one handed over
                      earliest goes, and the bag is then reconsidered from the
                      start. This is not a tidying detail. Putting a version of a
                      setting up where the worker had none takes every parcel
                      carrying the other branch of that setting out of reach, so
                      two parcels can each be ready with only one of them ever
                      going anywhere, and which one it is has to be settled.
"""


class Book(object):
    def __init__(self):
        self.who = []
        self.val = []
        self.up = []
        self.pic = []
        self.anc = []

    def add(self, s, val, up, pic):
        self.who.append(s)
        self.val.append(val)
        self.up.append(tuple(up))
        self.pic.append(pic)
        self.anc.append(None)
        return len(self.who) - 1

    def over(self, i):
        if self.anc[i] is None:
            got = set([i])
            for j in self.up[i]:
                got |= self.over(j)
            self.anc[i] = got
        return self.anc[i]

    def after(self, j, i):
        return i in self.over(j)


def _covered(book, pic, seen, carry):
    for s in pic:
        want = pic[s]
        have = seen.get(s)
        if have is not None and book.after(have, want):
            continue
        has = carry.get(s)
        if has is not None and book.after(has, want):
            continue
        return False
    return True


def _up(book, ent, seen):
    for s in ent:
        want = ent[s]
        have = seen.get(s)
        if have is not None:
            if book.after(have, want):
                continue
            if not book.after(want, have):
                return False
        if not _covered(book, book.pic[want], seen, ent):
            return False
    return True


def _first(book, bag, parc, seen):
    for no in bag:
        if _up(book, parc[no], seen):
            return no
    return None


def _settle(book, seen, bag, parc):
    moved = set()
    while True:
        no = _first(book, bag, parc, seen)
        if no is None:
            return moved
        bag.remove(no)
        ent = parc[no]
        for s in ent:
            want = ent[s]
            have = seen.get(s)
            if have == want:
                continue
            if have is None or book.after(want, have):
                seen[s] = want
                moved.add(s)


def _face(book, seen, s):
    if s not in seen:
        return "-"
    val = book.val[seen[s]]
    return "x" if val is None else str(val)


def play(text):
    book = Book()
    seen = {}
    bags = {}
    band = {}
    parc = {}
    rows = []
    step = 0

    def sit(w):
        if w not in seen:
            seen[w] = {}
            bags[w] = []
        return seen[w]

    def show(w):
        moved = _settle(book, sit(w), bags[w], parc)
        if moved:
            rows.append(("sh", step, w,
                         [(s, _face(book, seen[w], s)) for s in sorted(moved)]))

    for line in text.splitlines():
        bit = line.split()
        if not bit:
            continue
        step += 1
        kind = bit[0]
        if kind == "gp":
            band[bit[1]] = list(bit[2:])
        elif kind in ("wr", "rm"):
            view = sit(bit[1])
            here = view.get(bit[2])
            view[bit[2]] = book.add(bit[2],
                                    int(bit[3]) if kind == "wr" else None,
                                    () if here is None else (here,),
                                    dict((k, view[k]) for k in view))
        elif kind == "mg":
            view = sit(bit[1])
            no = int(bit[3])
            ent = parc.get(no, {})
            if bit[2] in view and bit[2] in ent and ent[bit[2]] != view[bit[2]]:
                a, b = view[bit[2]], ent[bit[2]]
                pic = dict((k, view[k]) for k in view)
                view[bit[2]] = book.add(bit[2], book.val[max(a, b)], (a, b), pic)
                show(bit[1])
        elif kind == "rd":
            rows.append(("rd", step, bit[1], bit[2],
                         _face(book, sit(bit[1]), bit[2])))
        elif kind == "pb":
            view = sit(bit[1])
            no = len(parc) + 1
            parc[no] = dict((k, view[k]) for k in band.get(bit[2], ())
                            if k in view)
        elif kind == "tk":
            sit(bit[1])
            bags[bit[1]].append(int(bit[2]))
            show(bit[1])
        else:
            raise ValueError(kind)

    tail = []
    for w in sorted(seen):
        tail.append((w, [(s, _face(book, seen[w], s)) for s in sorted(seen[w])]))
    return rows, tail
