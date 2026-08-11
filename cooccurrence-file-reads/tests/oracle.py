"""Ground truth, derived from the rules rather than from a clever algorithm.

`decide_definitional` is the definition written out: try every way of choosing
a code -- or nothing at all, where the summary says the field was sometimes
left unset -- for each field the file or the filter has anything to say about,
keep the choices every recorded pair agrees with, and see whether any of them
makes the filter come out true. Fields nothing mentions are left out of the
enumeration, which changes no answer: they are in no recorded pair and in no
condition, so any code will do for them. The small block is built so that no
more than four fields are ever mentioned, which is what makes this affordable
there and nowhere else.

`Truth` is the same decision arranged so the wide and timed blocks can be
graded at all. A grading case makes the two agree on fresh random instances
every run before the searching one is trusted.

Only root and the grading account can read this file.
"""

from casegen import CODES, COLUMNS, PAIRS, pair_name

TRUE = "T"
FALSE = "F"
UNKNOWN = "U"

FULL = (1 << CODES) - 1
NOTHING = 1 << CODES  # the seventeenth candidate: the field left unset

CMP = {
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "=": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
}

COLSET = set(COLUMNS)


def evaluate(node, row):
    """Three values, because a field with nothing in it answers nothing.

    A condition on an unset field is neither true nor false. `and` is false as
    soon as one arm is false and true only when every arm is true; `or` is true
    as soon as one arm is true and false only when every arm is false; `not`
    leaves the third value alone. The file is read on true, and on nothing else.
    """
    op = node["op"]
    if op == "and":
        soft = False
        for arg in node["args"]:
            got = evaluate(arg, row)
            if got == FALSE:
                return FALSE
            if got == UNKNOWN:
                soft = True
        return UNKNOWN if soft else TRUE
    if op == "or":
        soft = False
        for arg in node["args"]:
            got = evaluate(arg, row)
            if got == TRUE:
                return TRUE
            if got == UNKNOWN:
                soft = True
        return UNKNOWN if soft else FALSE
    if op == "not":
        got = evaluate(node["arg"], row)
        if got == UNKNOWN:
            return UNKNOWN
        return FALSE if got == TRUE else TRUE
    held = row.get(node["col"])
    if held is None:
        return UNKNOWN
    return TRUE if CMP[op](held, node["value"]) else FALSE


def filter_columns(node, into=None):
    if into is None:
        into = set()
    op = node["op"]
    if op == "and" or op == "or":
        for arg in node["args"]:
            filter_columns(arg, into)
    elif op == "not":
        filter_columns(node["arg"], into)
    else:
        into.add(node["col"])
    return into


def code_mask(op, value):
    keep = 0
    test = CMP[op]
    for code in range(CODES):
        if test(code, value):
            keep |= 1 << code
    return keep


def reachable(node, domains, sign):
    """Could this still come out `sign`, on what the domains permit? Each
    condition is asked on its own, so the answer is loose in the direction of
    yes, which is what makes a no worth acting on."""
    op = node["op"]
    if op == "and":
        if sign:
            return all(reachable(a, domains, True) for a in node["args"])
        return any(reachable(a, domains, False) for a in node["args"])
    if op == "or":
        if sign:
            return any(reachable(a, domains, True) for a in node["args"])
        return all(reachable(a, domains, False) for a in node["args"])
    if op == "not":
        return reachable(node["arg"], domains, not sign)
    keep = code_mask(op, node["value"])
    if not sign:
        keep = FULL & ~keep
    return bool(domains[node["col"]] & keep)


def require(node, sign, domains, moved, resting, picked):
    """Narrow the domains by the requirement that this comes out `sign`.

    `and` that has to be true and `or` that has to be false pass the whole
    requirement to every arm. The other way round it falls on the arms
    together: nothing is asked of any one of them until one arm is the only one
    left that could carry it. `not` flips which case this is. A condition
    carrying a requirement, either way round, cuts its field to codes -- an
    unset field answers neither true nor false, so it satisfies neither.

    A requirement still resting on several arms is left in `resting` for the
    search to settle, unless it already has, in which case `picked` names the
    arm it chose and the requirement passes whole to that one.
    """
    op = node["op"]
    if op == "not":
        return require(node["arg"], not sign, domains, moved, resting, picked)
    if op in ("and", "or"):
        if (op == "and") == sign:
            for arg in node["args"]:
                if not require(arg, sign, domains, moved, resting, picked):
                    return False
            return True
        chosen = picked.get(id(node))
        if chosen is not None:
            return require(chosen, sign, domains, moved, resting, picked)
        live = [a for a in node["args"] if reachable(a, domains, sign)]
        if not live:
            return False
        if len(live) == 1:
            return require(live[0], sign, domains, moved, resting, picked)
        resting.append((node, sign, live))
        return True
    keep = code_mask(op, node["value"])
    if not sign:
        keep = FULL & ~keep
    col = node["col"]
    cut = domains[col] & keep
    if cut == 0:
        return False
    if cut != domains[col]:
        domains[col] = cut
        moved.append(col)
    return True


def _candidates(entry, columns):
    unset = set(entry.get("unset") or [])
    out = {}
    for col in columns:
        values = list(range(CODES))
        if col in unset:
            values.append(None)
        out[col] = values
    return out


def _live_pairs(entry, columns):
    recorded = entry.get("pairs") or {}
    live = []
    for (x, y) in PAIRS:
        name = pair_name(x, y)
        if name in recorded and x in columns and y in columns:
            live.append((x, y, recorded[name]))
    return live


def mentioned(entry, filter_expr):
    """The fields the file or the filter has anything to say about."""
    cols = set()
    for name in (entry.get("pairs") or {}):
        cols.add(name[0])
        cols.add(name[1])
    cols |= filter_columns(filter_expr)
    return sorted(cols & COLSET)


def decide_definitional(entry, filter_expr):
    """Every choice, tried. Nothing here knows anything but the rules."""
    columns = mentioned(entry, filter_expr)
    if len(columns) > 5:
        raise AssertionError(
            "the definitional model was handed %d fields; it is only meant "
            "for the small block" % len(columns))
    candidates = _candidates(entry, columns)
    live = _live_pairs(entry, columns)

    row = {}

    def agrees():
        for (x, y, masks) in live:
            i = row.get(x)
            j = row.get(y)
            if i is None or j is None:
                continue
            if not (masks[i] >> j) & 1:
                return False
        return True

    # The pair check and the filter check stay two separate readings of the
    # rules, both made on a choice that is complete.
    def walk(at):
        if at == len(columns):
            return agrees() and evaluate(filter_expr, row) == TRUE
        col = columns[at]
        for value in candidates[col]:
            row[col] = value
            if walk(at + 1):
                del row[col]
                return True
        if col in row:
            del row[col]
        return False

    return walk(0)


class Truth:
    """The same decision, arranged so it can be afforded on the big blocks.

    Domains are seventeen-bit masks: one bit per code, and one more for the
    field left unset, which is a candidate only where the summary recorded one.
    A recorded pair says nothing about a choice where either side is unset, so
    the unset bit survives every narrowing, which is also why a pair whose other
    side can be unset prunes nothing at all before anything is committed.

    Everything that depends on the file alone is worked out once for the whole
    manifest. What a filter costs after that is the search.
    """

    def __init__(self, manifest):
        self.files = [self._prepare(entry) for entry in manifest]

    @staticmethod
    def _prepare(entry):
        recorded = entry.get("pairs") or {}
        unset = set(entry.get("unset") or []) & COLSET
        links = {c: [] for c in COLUMNS}
        checks = []
        for (x, y) in PAIRS:
            name = pair_name(x, y)
            table = recorded.get(name)
            if table is None:
                continue
            forward = [int(table[i]) & FULL for i in range(CODES)]
            backward = [0] * CODES
            for i, mask in enumerate(forward):
                bits = mask
                while bits:
                    low = bits & -bits
                    bits ^= low
                    backward[low.bit_length() - 1] |= 1 << i
            links[x].append((y, forward))
            links[y].append((x, backward))
            checks.append((x, y, forward))

        domains = {}
        for col in COLUMNS:
            domains[col] = FULL | (NOTHING if col in unset else 0)
        changed = True
        while changed:
            changed = False
            for col in COLUMNS:
                for (other, table) in links[col]:
                    if domains[other] & NOTHING:
                        continue
                    reach = 0
                    for code in range(CODES):
                        if table[code] & domains[other]:
                            reach |= 1 << code
                    cut = domains[col] & (reach | NOTHING)
                    if cut != domains[col]:
                        domains[col] = cut
                        changed = True
        return links, domains, checks

    @staticmethod
    def _spread(domains, links, worklist):
        """Arc consistency, worked outwards from the fields that just moved.

        A field that may still be unset constrains nobody, because a pair says
        nothing about a choice where either side is unset.
        """
        while worklist:
            col = worklist.pop()
            held = domains[col]
            if held & NOTHING:
                continue
            for (other, table) in links[col]:
                reach = 0
                for code in range(CODES):
                    if (held >> code) & 1:
                        reach |= table[code]
                cut = domains[other] & (reach | NOTHING)
                if cut != domains[other]:
                    if cut == 0:
                        return False
                    domains[other] = cut
                    worklist.append(other)
        return True

    def _settle(self, filter_expr, domains, links, seed, picked):
        """Narrowing to a fixed point. Hands back the requirements still
        resting on more than one arm, or None if none of them can be met."""
        worklist = list(seed)
        while True:
            if worklist and not self._spread(domains, links, worklist):
                return None
            moved = []
            resting = []
            if not require(filter_expr, True, domains, moved, resting, picked):
                return None
            if not moved:
                return resting
            worklist = moved

    def decide(self, prepared, filter_expr, needed):
        links, base, checks = prepared
        domains = dict(base)
        resting = self._settle(filter_expr, domains, links, [], {})
        if resting is None:
            return False
        # Only fields taking part in a recorded pair are ever committed. Once
        # nothing is resting on several arms, every requirement the filter
        # makes has landed on a field and cut it to the codes that meet it, so
        # the filter comes out true on any choice inside the domains; a field
        # in no recorded pair has nothing left to settle. The choice handed to
        # the definitional checks below is still complete, and it is those
        # checks, not this argument, that decide whether a file is read.
        wanted = [c for c in COLUMNS if links[c]]
        return self._place(filter_expr, wanted, domains, links, checks,
                           resting, {}, needed)

    def _place(self, filter_expr, wanted, domains, links, checks, resting,
               picked, needed):
        if resting:
            # An `or` that has to come out true is two or three arms wide and
            # a field is sixteen candidates wide, so settle the arms first:
            # picking one turns a requirement that narrowed nothing into one
            # that narrows every field it names.
            node, sign, live = min(resting, key=lambda item: len(item[2]))
            key = id(node)
            for arm in live:
                chosen = dict(picked)
                chosen[key] = arm
                narrowed = dict(domains)
                left = self._settle(filter_expr, narrowed, links, [], chosen)
                if left is None:
                    continue
                if self._place(filter_expr, wanted, narrowed, links, checks,
                               left, chosen, needed):
                    return True
            return False
        col = None
        for candidate in wanted:
            if bin(domains[candidate]).count("1") > 1:
                col = candidate
                break
        if col is None:
            # Every field the file or the filter speaks about is down to one
            # candidate. Rather than take propagation's word for it, read the
            # choice out and put it through the same two checks the
            # definitional model applies, so that a mistake anywhere in the
            # narrowing can only ever lose a witness, never invent one.
            row = {}
            for name in set(wanted) | set(needed):
                held = domains[name]
                if held == NOTHING:
                    row[name] = None
                else:
                    low = (held & FULL) & -(held & FULL)
                    row[name] = None if low == 0 else low.bit_length() - 1
            for (x, y, table) in checks:
                i = row.get(x)
                j = row.get(y)
                if i is None or j is None:
                    continue
                if not (table[i] >> j) & 1:
                    return False
            return evaluate(filter_expr, row) == TRUE
        bits = domains[col]
        while bits:
            low = bits & -bits
            bits ^= low
            narrowed = dict(domains)
            narrowed[col] = low
            left = self._settle(filter_expr, narrowed, links, [col], picked)
            if left is None:
                continue
            if self._place(filter_expr, wanted, narrowed, links, checks, left,
                           picked, needed):
                return True
        return False

    def plan(self, filter_expr):
        needed = filter_columns(filter_expr)
        return [i for i, prepared in enumerate(self.files)
                if self.decide(prepared, filter_expr, needed)]


def plan_definitional(manifest, filter_expr):
    return [i for i, e in enumerate(manifest)
            if decide_definitional(e, filter_expr)]


def plan_search(manifest, filter_expr):
    return Truth(manifest).plan(filter_expr)
