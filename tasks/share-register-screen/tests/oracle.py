"""A second implementation of the determination, written from the specification.

It shares no code with the tree under test and is deliberately built differently at every
step, so that agreement between the two is evidence about the specification rather than
about one author's habits:

  * the filings are replayed into a flat list of movements and folded at the end, instead
    of being applied to a running book;
  * the board is filled by taking the largest of a set of exact rationals, instead of by
    the integer cross-multiplication the tree uses;
  * the list is closed by a worklist that revisits a company whenever anything changes,
    instead of by repeated whole passes;
  * nominee chains are flattened up front into a single map, instead of walked per lookup.

The verifier believes no expected record that this file does not reproduce.
"""

from __future__ import annotations

from fractions import Fraction

GAP = "-"
MARK = "*"
LUMP = "\x01"

WIDTH = {"co": 2, "cl": 3, "is": 4, "mv": 5, "nm": 2, "nx": 1, "pg": 1}


class Reject(Exception):
    pass


def _parse(text):
    rows = []
    for n, raw in enumerate(text.splitlines(), 1):
        bits = raw.split()
        if not bits:
            continue
        if bits[0] not in WIDTH or len(bits) - 1 != WIDTH[bits[0]]:
            raise Reject("line %d" % n)
        rows.append(bits)
    return rows


def _state(text):
    order, seats, weight = [], {}, {}
    moves, nomacts, named = [], [], []
    for bits in _parse(text):
        op = bits[0]
        if op == "co":
            if bits[1] in seats:
                raise Reject("repeat %s" % bits[1])
            order.append(bits[1])
            seats[bits[1]] = int(bits[2])
        elif op == "cl":
            if bits[1] not in seats:
                raise Reject("unknown %s" % bits[1])
            weight[(bits[1], bits[2])] = int(bits[3])
        elif op == "is":
            if (bits[1], bits[2]) not in weight:
                raise Reject("unknown class")
            moves.append((bits[1], bits[2], bits[4], int(bits[3])))
        elif op == "mv":
            moves.append((bits[1], bits[2], bits[4], -int(bits[3])))
            moves.append((bits[1], bits[2], bits[5], int(bits[3])))
        elif op == "nm":
            nomacts.append((bits[1], bits[2]))
        elif op == "nx":
            nomacts.append((bits[1], None))
        else:
            if bits[1] not in named:
                named.append(bits[1])
    return order, seats, weight, moves, nomacts, named


def _sightings(text):
    seen = []
    for bits in _parse(text):
        op = bits[0]
        picks = {"co": [1], "is": [4], "mv": [5], "nm": [1, 2], "pg": [1]}.get(op, [])
        for i in picks:
            if bits[i] not in seen:
                seen.append(bits[i])
    return seen


def _running(moves, weight, order, seats):
    stock = {}
    for co, kind, who, n in moves:
        key = (co, kind, who)
        stock[key] = stock.get(key, 0) + n
        if stock[key] < 0:
            raise Reject("short %s" % (key,))
    votes = {c: {} for c in order}
    for (co, kind, who), n in sorted(stock.items()):
        if n <= 0 or who == co:
            continue
        w = weight[(co, kind)] * n
        if w <= 0:
            continue
        votes[co][who] = votes[co].get(who, 0) + w
    return votes


def _principals(nomacts):
    live = {}
    for who, to in nomacts:
        if to is None:
            live.pop(who, None)
        else:
            live[who] = to
    flat = {}
    for who in sorted(live):
        walked = [who]
        step = who
        while step in live:
            step = live[step]
            if step in walked:
                step = walked[0]
                break
            walked.append(step)
        flat[who] = step
    return flat


def _board(hands, count):
    taken = {k: 0 for k in hands if hands[k] > 0}
    out = []
    for _ in range(count):
        best, score = None, None
        for k in sorted(taken):
            here = Fraction(hands[k], taken[k] + 1)
            if score is None or here > score:
                best, score = k, here
        if best is None:
            out.append(GAP)
        else:
            taken[best] += 1
            out.append(best)
    return out


def determine(text):
    order, seats, weight, moves, nomacts, named = _state(text)
    votes = _running(moves, weight, order, seats)
    flat = _principals(nomacts)
    seen = _sightings(text)

    def caster(who):
        return flat.get(who, who)

    def hands_for(co, listed):
        out = {}
        for who in sorted(votes[co]):
            key = caster(who)
            if key == co:
                # The company's own stock, whoever the register records it against.
                continue
            if key in listed:
                key = LUMP
            out[key] = out.get(key, 0) + votes[co][who]
        return out

    listed = set(named)
    queue = list(order)
    while queue:
        co = queue.pop(0)
        if co in listed:
            continue
        board = _board(hands_for(co, listed), seats[co])
        if 2 * board.count(LUMP) > seats[co]:
            listed.add(co)
            queue = list(order)

    rows = []
    for co in order:
        board = _board(hands_for(co, listed), seats[co])
        got = board.count(LUMP)
        cells = []
        for k in board:
            if k == GAP:
                cells.append(GAP)
            elif k == LUMP or k in listed or k not in seen:
                cells.append(MARK)
            else:
                cells.append(k)
        rows.append([co, 1 if co in listed else 0, got, seats[co], cells])
    return rows
