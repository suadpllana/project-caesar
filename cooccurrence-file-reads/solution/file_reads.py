"""Reference solution for cooccurrence-file-reads.

A file is worth reading when there is one choice -- a code for every field, or
nothing at all where the summary recorded that the field was sometimes left
unset -- that every recorded pair agrees with and that the filter comes out
true on. Three things about that make the obvious implementation wrong.

The first is that agreement is recorded between fields two at a time and the
choice has to hold for all of them at once. Two fields agreeing, and each of
them agreeing with a third, does not give three that agree together, so
narrowing what each field may hold and declaring victory when nothing has
emptied says read where the truth says skip. Narrowing is a filter here and
never a verdict: it makes the search small, and then the search has to be run.

The second is the unset field. A pair says nothing about a choice where either
side is unset, so an unset field escapes every pair it takes part in -- which
is why a pair whose far side may be unset prunes nothing at all until something
is committed, and why a file whose recorded pairs rule out every code can still
have to be read.

The third is that a condition on an unset field is neither true nor false, and
the file is read on true and on nothing else. So the filter is settled in three
values, `not` leaves the third one alone, and a condition that has to come out
false still needs a code, because an unset field will not deliver false either.

What is left is a search, and the search has to be cheap, because the same
manifest is asked filter after filter. Two things make it cheap. Everything
depending on the file alone is done once when the reader is built: both
directions of every recorded pair, who neighbours whom, and the domains
narrowed to a fixed point. And the filter is not something the search consults
at the end but something it propagates from at every step -- an `and` that has
to be true hands that requirement to each of its arms, an `or` that has to be
true and has only one arm left that could be hands it to that arm, and a
condition carrying a requirement cuts its field's domain down to the codes that
meet it. Filter narrowing and pair narrowing are run against each other to a
fixed point before any code is committed, which is what stops the search from
walking a space it has no business in.
"""

CODES = 16
COLUMNS = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l"]
NCOL = len(COLUMNS)
INDEX = {c: i for i, c in enumerate(COLUMNS)}
FULL = (1 << CODES) - 1
NOTHING = 1 << CODES
ANY = FULL | NOTHING

TESTS = {
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "=": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
}

LEAF, AND, OR, NOT = 0, 1, 2, 3

_MASKS = {}


def _codes_where(op, value):
    key = (op, value)
    got = _MASKS.get(key)
    if got is None:
        test = TESTS[op]
        got = 0
        for code in range(CODES):
            if test(code, value):
                got |= 1 << code
        _MASKS[key] = got
    return got


def _compile(node):
    """The filter as nested tuples, every condition reduced to two masks: the
    codes that make it true, and the codes that make it false. Neither holds
    the unset field, which makes a condition neither."""
    op = node["op"]
    if op == "and":
        return (AND, tuple(_compile(a) for a in node["args"]))
    if op == "or":
        return (OR, tuple(_compile(a) for a in node["args"]))
    if op == "not":
        return (NOT, _compile(node["arg"]))
    yes = _codes_where(op, node["value"])
    return (LEAF, INDEX[node["col"]], yes, FULL & ~yes)


def _columns_used(node, into):
    kind = node[0]
    if kind == LEAF:
        into.add(node[1])
    elif kind == NOT:
        _columns_used(node[1], into)
    else:
        for arg in node[1]:
            _columns_used(arg, into)
    return into


def _can_be(node, domains, sign):
    """Could this come out `sign` on what the domains still permit?

    Every condition is asked on its own, so two conditions on one field are not
    held to the same code and the answer is looser than the truth. It can only
    say yes too often, which is what makes a no safe to act on.
    """
    kind = node[0]
    if kind == LEAF:
        return bool(domains[node[1]] & (node[2] if sign else node[3]))
    if kind == NOT:
        return _can_be(node[1], domains, not sign)
    if (kind == AND) == sign:
        for arg in node[1]:
            if not _can_be(arg, domains, sign):
                return False
        return True
    for arg in node[1]:
        if _can_be(arg, domains, sign):
            return True
    return False


def _require(node, sign, domains, fresh):
    """Cut the domains down by the requirement that this comes out `sign`.

    An `and` that has to be true, and an `or` that has to be false, hand the
    requirement whole to every arm. The other way round the requirement falls
    on the arms together, so it says nothing about any one of them until only
    one arm is left that could carry it, and then it says everything. `not`
    flips which case we are in. A condition carrying a requirement cuts its
    field to the codes that meet it, and never leaves room for the field to be
    unset, whichever way round the requirement is.

    False means the requirement cannot be met at all.
    """
    kind = node[0]
    if kind == LEAF:
        col = node[1]
        keep = domains[col] & (node[2] if sign else node[3])
        if keep == 0:
            return False
        if keep != domains[col]:
            domains[col] = keep
            fresh.append(col)
        return True
    if kind == NOT:
        return _require(node[1], not sign, domains, fresh)
    args = node[1]
    if (kind == AND) == sign:
        for arg in args:
            if not _require(arg, sign, domains, fresh):
                return False
        return True
    only = None
    for arg in args:
        if _can_be(arg, domains, sign):
            if only is not None:
                return True
            only = arg
    if only is None:
        return False
    return _require(only, sign, domains, fresh)


def _revise(domains, links, queue):
    """Arc consistency, from the fields whose domains have just moved."""
    while queue:
        col = queue.pop()
        held = domains[col]
        if held & NOTHING:
            continue
        for (other, forward, whole) in links[col]:
            if held == FULL:
                reach = whole
            else:
                reach = 0
                bits = held
                while bits:
                    low = bits & -bits
                    bits ^= low
                    reach |= forward[low.bit_length() - 1]
            there = domains[other]
            keep = there & (reach | NOTHING)
            if keep != there:
                if keep == 0:
                    return False
                domains[other] = keep
                queue.append(other)
    return True


def _propagate(root, domains, links, seed):
    """Run the filter's requirements and the recorded pairs against each other
    until neither has anything left to say."""
    queue = list(seed)
    while True:
        if queue and not _revise(domains, links, queue):
            return False
        fresh = []
        if not _require(root, True, domains, fresh):
            return False
        if not fresh:
            return True
        queue = fresh


def _bits(mask):
    out = []
    while mask:
        low = mask & -mask
        mask ^= low
        out.append(low.bit_length() - 1)
    return out


def _search(root, order, domains, links):
    """Commit a field at a time, narrowest first. When every field the file or
    the filter speaks about holds exactly one candidate and propagation is
    still standing, the pairs all agree and the filter is true: that choice is
    the witness the question asks for."""
    pick = -1
    width = NCOL * CODES
    for col in order:
        here = bin(domains[col]).count("1")
        if 1 < here < width:
            pick, width = col, here
    if pick < 0:
        return True
    for value in _bits(domains[pick]):
        narrowed = list(domains)
        narrowed[pick] = 1 << value
        if _propagate(root, narrowed, links, (pick,)) and _search(
                root, order, narrowed, links):
            return True
    return False


class Reader:
    def __init__(self, manifest):
        self.files = [self._prepare(entry) for entry in manifest]

    @staticmethod
    def _prepare(entry):
        """Both directions of every recorded pair, who neighbours whom, and
        the domains narrowed as far as the file on its own can narrow them.
        None for a file no choice at all can be made for."""
        recorded = entry.get("pairs") or {}
        unset = entry.get("unset") or []
        links = [[] for _ in range(NCOL)]
        for name, table in recorded.items():
            if not isinstance(name, str) or len(name) != 2:
                continue
            x = INDEX.get(name[0])
            y = INDEX.get(name[1])
            if x is None or y is None or x == y:
                continue
            forward = [0] * CODES
            for i in range(min(CODES, len(table))):
                forward[i] = int(table[i]) & FULL
            backward = [0] * CODES
            for i, mask in enumerate(forward):
                bits = mask
                while bits:
                    low = bits & -bits
                    bits ^= low
                    backward[low.bit_length() - 1] |= 1 << i
            links[x].append((y, forward, _union(forward)))
            links[y].append((x, backward, _union(backward)))

        domains = [FULL] * NCOL
        for name in unset:
            i = INDEX.get(name)
            if i is not None:
                domains[i] |= NOTHING
        if not _revise(domains, links, list(range(NCOL))):
            return None

        touched = set(c for c in range(NCOL) if links[c])
        return links, domains, touched

    def files_to_read(self, filter_expr):
        root = _compile(filter_expr)
        order = _columns_used(root, set())
        out = []
        for index, prepared in enumerate(self.files):
            if prepared is None:
                continue
            links, base, touched = prepared
            domains = list(base)
            if not _propagate(root, domains, links, ()):
                continue
            if _search(root, sorted(touched | order), domains, links):
                out.append(index)
        return out


def _union(table):
    whole = 0
    for mask in table:
        whole |= mask
    return whole


def files_to_read(manifest, filter_expr):
    return Reader(manifest).files_to_read(filter_expr)
