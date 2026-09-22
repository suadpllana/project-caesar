"""An independent settlement of the same contract, written apart from the reference.

The reference keeps the waiting branches in a heap and the history in dicts of lists read
through a counter per axis. This keeps the waiting branches in one list held in order with
`bisect.insort`, the branches themselves as plain lists, and the history in flat arrays
indexed by line position. Both are affordable and neither is the other, so agreement over a
large shaped population is what says the verifier grades the contract and not one
implementation.

The rules, in the order a run meets them:

  1  a command is matched to the recorded command at its own position among those of its
     kind; other kinds do not shift that count, and once the live side is open nothing is
     matched at all
  2  a recorded command naming something else ends the run where it happens
  3  a matched command's answer is the recorded answer at its position among those of that
     kind and name together, and it carries the position of its own line
  4  a branch that waits goes down with a mark: the position of the line that releases it,
     or no mark when the history never recorded one
  5  a branch waiting for a signal claims one as it goes down, per tag, in recorded order
  6  a branch that can run without waiting goes before one that has to be woken; among the
     first, the lowest numbered; among the second, the smallest mark
  7  the live side opens when nothing can run and nothing can be woken; it is said once,
     every waiting branch is released in number order, and from then on nothing waits
  8  a result the history does not carry comes off the run file's list, in the order the
     branches take them
  9  an unrecorded marker is zero while the history can still move the run, and the body's
     own value once the live side is open
 10  branch zero ending ends the run; a recorded command no command matched is a failure
     naming the earliest of them, and nothing else in the history is
 11  a run past the step ceiling ends over
"""
import bisect

KINDS = {"call": "call", "fire": "call", "spawn": "child", "nap": "timer"}
AWAITS = ("call", "spawn", "nap")
CEIL = 200000

PC, ACC, DUE, STATE = 0, 1, 2, 3


def _split(lines):
    body, log, feed = [], [], []
    for raw in lines:
        row = raw.split()
        if not row:
            continue
        if row[0] == "b":
            body.append(row[1:])
        elif row[0] == "e":
            log.append(row[1:])
        elif row[0] == "r":
            feed.append(int(row[1]))
    return body, log, feed


def expect(lines):
    body, log, feed = _split(lines)

    # --- the history, one pass into flat arrays -------------------------------------
    go_kind, go_name, go_rank, go_pos = [], [], [], []
    per_kind, by_kind = {}, {}
    ok_at, sig_at, ch_at = {}, {}, {}
    for pos, row in enumerate(log):
        if row[0] == "go":
            kind = row[1]
            rank = per_kind.get(kind, 0)
            per_kind[kind] = rank + 1
            by_kind.setdefault(kind, []).append(len(go_kind))
            go_kind.append(kind)
            go_name.append(row[2])
            go_rank.append(rank)
            go_pos.append(pos)
        elif row[0] == "ok":
            ok_at.setdefault((row[1], row[2]), []).append((pos, int(row[3])))
        elif row[0] == "sig":
            sig_at.setdefault(row[1], []).append((pos, int(row[2])))
        elif row[0] == "ch":
            ch_at.setdefault(row[1], []).append(int(row[2]))
    matched = bytearray(len(go_kind))

    labels = {}
    for at, row in enumerate(body):
        if row[0] == "lab":
            labels[row[1]] = at

    out = []
    live = False
    steps = 0
    issued, paired, sig_used, ch_used = {}, {}, {}, {}
    feed_at = [0]
    claim = {}
    outstanding = {}                                  # bid -> [rec, ...]
    branches = []                                     # [pc, acc, due, state]
    ready = []                                        # bids able to run, kept sorted
    waiting = []                                      # (mark, bid), kept sorted
    idle = []                                         # bids with no mark

    def spare():
        value = feed[feed_at[0]] if feed_at[0] < len(feed) else 0
        feed_at[0] += 1
        return value

    def start(pc):
        branches.append([pc, 0, None, "ready"])
        bisect.insort(ready, len(branches) - 1)
        return len(branches) - 1

    def leftover():
        for at in range(len(go_kind)):
            if not matched[at]:
                return "drift left %s %d" % (go_kind[at], go_rank[at])
        return None

    def settle(bid, due):
        """Hand a waiting branch what it was waiting for, and say so."""
        what, load = due
        if what == "ok":
            kind, idx, value, _pos = load
            value = spare() if value is None else value
            row = outstanding.get(bid) or []
            for at in range(len(row)):
                if row[at] is load:
                    row.pop(at)
                    break
            branches[bid][ACC] = value
            out.append("%d ok %s %d %d" % (bid, kind, idx, value))
        else:
            if bid in claim:
                value = claim.pop(bid)
            else:
                seen = sig_used.get(load, 0)
                have = sig_at.get(load, ())
                if seen < len(have):
                    sig_used[load] = seen + 1
                    value = have[seen][1]
                else:
                    value = spare()
            branches[bid][ACC] = value
            out.append("%d sig %s %d" % (bid, load, value))

    def mark_for(bid, due):
        what, load = due
        if what == "ok":
            return load[3]
        seen = sig_used.get(load, 0)
        have = sig_at.get(load, ())
        if seen >= len(have):
            return None
        sig_used[load] = seen + 1
        claim[bid] = have[seen][1]
        return have[seen][0]

    def lay_down(bid, due):
        branches[bid][DUE] = due
        branches[bid][STATE] = "parked"
        mark = mark_for(bid, due)
        if mark is None:
            bisect.insort(idle, bid)
        else:
            bisect.insort(waiting, (mark, bid))

    start(0)

    while True:
        if ready:
            bid = ready.pop(0)
        elif waiting:
            bid = waiting.pop(0)[1]
        else:
            if live:
                row = leftover()
                out.append(row if row else "fin 0")
                return out
            live = True
            out.append("live")
            for held in idle:
                branches[held][STATE] = "ready"
                bisect.insort(ready, held)
            idle = []
            continue
        branches[bid][STATE] = "running"

        if branches[bid][DUE] is not None:
            due = branches[bid][DUE]
            branches[bid][DUE] = None
            settle(bid, due)

        while True:
            steps += 1
            if steps > CEIL:
                out.append("over")
                return out
            if branches[bid][PC] >= len(body):
                out.append("%d end %d" % (bid, branches[bid][ACC]))
                branches[bid][STATE] = "ended"
                if bid == 0:
                    row = leftover()
                    out.append(row if row else "fin %d" % branches[bid][ACC])
                    return out
                break
            row = body[branches[bid][PC]]
            op = row[0]
            branches[bid][PC] += 1

            if op in KINDS:
                kind = KINDS[op]
                name = row[1]
                at = issued.get(kind, 0)
                issued[kind] = at + 1
                hit = None
                if not live:
                    of_kind = by_kind.get(kind, ())
                    if at < len(of_kind):
                        hit = of_kind[at]
                if hit is not None:
                    if go_name[hit] != name:
                        out.append("drift %s %d %s %s" % (kind, at, go_name[hit], name))
                        return out
                    matched[hit] = 1
                    key = (kind, name)
                    seen = paired.get(key, 0)
                    paired[key] = seen + 1
                    answers = ok_at.get(key, ())
                    if seen < len(answers):
                        pos, value = answers[seen]
                    else:
                        pos, value = None, None
                else:
                    pos, value = None, None
                rec = [kind, at, value, pos]
                out.append("%d go %s %d %s" % (bid, kind, at, name))
                outstanding.setdefault(bid, []).append(rec)
                if op in AWAITS:
                    if live:
                        settle(bid, ("ok", rec))
                    else:
                        lay_down(bid, ("ok", rec))
                        break
            elif op == "take":
                held = outstanding.get(bid) or []
                if held:
                    if live:
                        settle(bid, ("ok", held[0]))
                    else:
                        lay_down(bid, ("ok", held[0]))
                        break
            elif op == "wait":
                if live:
                    settle(bid, ("sig", row[1]))
                else:
                    lay_down(bid, ("sig", row[1]))
                    break
            elif op == "fork":
                out.append("%d fork %d" % (bid, start(labels[row[1]])))
            elif op == "mark":
                key = row[1]
                seen = ch_used.get(key, 0)
                have = ch_at.get(key, ())
                if seen < len(have):
                    ch_used[key] = seen + 1
                    branches[bid][ACC] = have[seen]
                else:
                    branches[bid][ACC] = int(row[2]) if live else 0
                out.append("%d ver %s %d" % (bid, key, branches[bid][ACC]))
            elif op == "add":
                branches[bid][ACC] += int(row[1])
            elif op == "set":
                branches[bid][ACC] = int(row[1])
            elif op == "jz":
                if branches[bid][ACC] == 0:
                    branches[bid][PC] = labels[row[1]]
            elif op == "jnz":
                if branches[bid][ACC] != 0:
                    branches[bid][PC] = labels[row[1]]
            elif op == "jmp":
                branches[bid][PC] = labels[row[1]]
            elif op == "end":
                out.append("%d end %d" % (bid, branches[bid][ACC]))
                branches[bid][STATE] = "ended"
                if bid == 0:
                    row = leftover()
                    out.append(row if row else "fin %d" % branches[bid][ACC])
                    return out
                break
