"""An independent implementation of the decode-search contract.

Written from the frozen contract rather than from the reference under `solution/`, and with
different structures throughout: a beam is its whole token tuple together with a plain set of
the spans that tuple holds, the kept set lends spans through a count per span maintained as
members enter and leave, and selection is an explicit walk down a sorted list. The reference
keeps a beam's sequence as a link to its parent, its spans as an integer bit set, and the lent
spans as those bit sets combined; nothing here shares a line with it.

`expect(lines)` returns exactly what `/app/run_beam.py` must print for the program.
"""


def _read(lines):
    """The one `cfg` line, the scoring rows, and the requests, in file order."""
    cfg, rows, asks = None, [], []
    for raw in lines:
        part = raw.split()
        if not part:
            continue
        if part[0] == "cfg":
            cfg = [int(x) for x in part[1:7]]
        elif part[0] == "sc":
            rows.append((int(part[1]), int(part[2]), int(part[3])))
        elif part[0] == "ask":
            asks.append((part[1], tuple(int(x) for x in part[2:])))
    return cfg, rows, asks


def _windows(seq, n):
    """Every n-token window of a sequence, as a set; empty while the sequence is too short."""
    return {tuple(seq[i:i + n]) for i in range(len(seq) - n + 1)}


def _worst(mem):
    """The member the kept set gives up first: lowest final, then longest, then latest in."""
    return max(mem, key=lambda one: (-one["fin"], one["ln"], one["order"]))


def _search(name, prompt, cfg, rows, out):
    w, n, floor, pen, cap, ceiling = cfg
    top = max((score for _a, _b, score in rows), default=0)

    # Continuations and the stop edge, read off the row list wherever they are wanted.
    def go(ctx):
        return sorted((b, score) for a, b, score in rows if a == ctx and b != 0)

    def quits(ctx):
        for a, b, score in rows:
            if a == ctx and b == 0:
                return score
        return None

    out.append("ask %s" % name)
    plen = len(prompt)
    # A beam: its score, its whole token tuple, and the spans that tuple holds.
    beams = [{"raw": 0, "seq": tuple(prompt), "span": _windows(prompt, n)}]
    mem, lent, made = [], {}, 0

    step = 0
    while True:
        step += 1

        # Pass one. Every beam that may stop does so, in slot order, before anything is ranked.
        for beam in beams:
            ln = len(beam["seq"]) - plen
            if ln < floor:
                continue
            add = quits(beam["seq"][-1])
            if add is None:
                continue
            made += 1
            one = {"fin": beam["raw"] + add - pen * ln, "ln": ln, "order": made,
                   "seq": beam["seq"], "span": beam["span"]}
            mem.append(one)
            for span in one["span"]:
                lent[span] = lent.get(span, 0) + 1
            out.append("shut %d %d %d" % (step, ln, one["fin"]))
            while len(mem) > cap:
                went = _worst(mem)
                mem.remove(went)
                for span in went["span"]:
                    lent[span] -= 1
                    if lent[span] == 0:
                        del lent[span]
                out.append("gone %d %d %d" % (step, went["ln"], went["fin"]))

        # Pass two. A continuation is refused by the beam's own sequence or by a lent span.
        cands = []
        for slot, beam in enumerate(beams):
            seq, held = beam["seq"], beam["span"]
            head = seq[len(seq) - n + 1:] if n > 1 else ()
            long_enough = len(seq) + 1 >= n
            for tok, add in go(seq[-1]):
                if long_enough:
                    span = head + (tok,)
                    if span in held or span in lent:
                        continue
                cands.append((beam["raw"] + add, slot, tok, slot))

        # Pass three. Down the ranking, one beam per final token, at most w of them.
        cands.sort(key=lambda one: (-one[0], one[1], one[2]))
        took, used = [], set()
        for cand in cands:
            if cand[2] in used:
                continue
            used.add(cand[2])
            took.append(cand)
            if len(took) == w:
                break

        # Pass four. Nothing taken, the ceiling, or a reach that cannot pass the worst member.
        why = None
        if not took:
            why = "dry"
        elif step >= ceiling:
            why = "cap"
        elif len(mem) >= cap:
            best = max(one[0] for one in took)
            low = min(one["fin"] for one in mem)
            if best - pen * step + max(0, top - pen) * (ceiling - step) <= low:
                why = "bound"
        if why is not None:
            out.append("halt %d %s" % (step, why))
            break

        grown = []
        for raw, _slot, tok, parent in took:
            old = beams[parent]
            seq = old["seq"] + (tok,)
            held = old["span"]
            if len(seq) >= n:
                held = held | {seq[len(seq) - n:]}
            grown.append({"raw": raw, "seq": seq, "span": held})
        beams = grown

    for pos, one in enumerate(sorted(mem, key=lambda x: (-x["fin"], x["ln"], x["order"]))):
        tail = "".join(" %d" % x for x in one["seq"][plen:])
        out.append("hyp %d %d %d%s" % (pos, one["fin"], one["ln"], tail))


def expect(lines):
    cfg, rows, asks = _read(lines)
    out = []
    for name, prompt in asks:
        _search(name, prompt, cfg, rows, out)
    return out
