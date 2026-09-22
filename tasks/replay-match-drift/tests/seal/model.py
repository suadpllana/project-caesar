"""An independent settlement of the same contract, written apart from the reference.

The reference under solution/ keeps the log in dicts of lists and reads them through a
counter per axis; this walks the log once into flat arrays indexed by log position, holds
the outstanding commands as plain tuples and tracks what was matched in a bytearray. The
two agree on every graded program or the task is not asserting a contract, it is asserting
an implementation.

The rules, in the order a run meets them:

  1  a command is matched to the recorded `go` at its own position among the `go` events of
     its kind; other kinds do not shift that count
  2  a recorded slot naming something else ends the run at once
  3  the first command whose kind has run out of recorded slots opens the live side, once
     for the whole run, and nothing after it consults the log for a slot
  4  a replayed command's answer is the recorded `ok` at its position among the `ok` events
     of its kind and name together
  5  a live command's answer is the next value the run file offers, and counts as having
     arrived after every recorded one
  6  `join` takes the outstanding command issued earliest, `race` the one answered earliest
  7  a command whose answer is not recorded stops the run
  8  a signal is taken per tag, in recorded order, on either side of the boundary
  9  an unrecorded marker is zero while replaying and the body's own value once live
 10  when the body finishes, a recorded command it never issued is a failure naming the
     earliest of them; nothing else in the log is
 11  a body that runs past the step ceiling ends over
"""

KINDS = {"call": "call", "fire": "call", "spawn": "child", "open": "child", "nap": "timer"}
TAKING = ("call", "spawn", "nap")
CEIL = 200000
LATER = 1 << 30


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

    # One pass over the log fills every index the rules read.
    go_kind, go_name, go_rank = [], [], []       # parallel arrays over recorded commands
    go_pos = []
    per_kind = {}
    ok_at = {}                                    # (kind, name) -> [(pos, value)]
    sig_at = {}                                   # tag -> [value]
    ch_at = {}                                    # key -> [value]
    for pos, row in enumerate(log):
        if row[0] == "go":
            kind = row[1]
            rank = per_kind.get(kind, 0)
            per_kind[kind] = rank + 1
            go_kind.append(kind)
            go_name.append(row[2])
            go_rank.append(rank)
            go_pos.append(pos)
        elif row[0] == "ok":
            ok_at.setdefault((row[1], row[2]), []).append((pos, int(row[3])))
        elif row[0] == "sig":
            sig_at.setdefault(row[1], []).append(int(row[2]))
        elif row[0] == "ch":
            ch_at.setdefault(row[1], []).append(int(row[2]))

    # go entries of one kind, in log order, so rule 1 is a list index.
    by_kind = {}
    for at in range(len(go_kind)):
        by_kind.setdefault(go_kind[at], []).append(at)
    taken = bytearray(len(go_kind))

    labels = {}
    for at, row in enumerate(body):
        if row[0] == "lab":
            labels[row[1]] = at

    out = []
    acc = 0
    pc = 0
    steps = 0
    live = False
    issued = {}                                   # kind -> how many commands issued
    paired = {}                                   # (kind, name) -> how many answers taken
    sig_used = {}
    ch_used = {}
    feed_at = 0
    late = 0
    pending = []                                  # [kind, idx, value, pos]

    def leftover():
        for at in range(len(go_kind)):
            if not taken[at]:
                return "drift left %s %d" % (go_kind[at], go_rank[at])
        return None

    while pc < len(body):
        steps += 1
        if steps > CEIL:
            out.append("over")
            return out
        row = body[pc]
        op = row[0]
        pc += 1

        if op in KINDS:
            kind = KINDS[op]
            name = row[1]
            idx = issued.get(kind, 0)
            issued[kind] = idx + 1
            hit = None
            if not live:
                row_of_kind = by_kind.get(kind, ())
                if idx < len(row_of_kind):
                    hit = row_of_kind[idx]
                else:
                    live = True
                    out.append("live")
            if hit is not None:
                if go_name[hit] != name:
                    out.append("drift %s %d %s %s" % (kind, idx, go_name[hit], name))
                    return out
                taken[hit] = 1
                key = (kind, name)
                seen = paired.get(key, 0)
                paired[key] = seen + 1
                answers = ok_at.get(key, ())
                if seen < len(answers):
                    pos, value = answers[seen]
                else:
                    pos, value = None, None
            else:
                value = feed[feed_at] if feed_at < len(feed) else 0
                feed_at += 1
                late += 1
                pos = LATER + late
            out.append("go %s %d %s" % (kind, idx, name))
            if op in TAKING:
                if value is None:
                    out.append("hold %s %d" % (kind, idx))
                    return out
                acc = value
                out.append("ok %s %d %d" % (kind, idx, value))
            else:
                pending.append([kind, idx, value, pos])

        elif op in ("join", "race"):
            if not pending:
                out.append("hold none")
                return out
            if op == "join":
                pick = 0
            else:
                pick = None
                for at, rec in enumerate(pending):
                    if rec[3] is None:
                        continue
                    if pick is None or rec[3] < pending[pick][3]:
                        pick = at
                if pick is None:
                    pick = 0
            kind, idx, value, _pos = pending[pick]
            if value is None:
                out.append("hold %s %d" % (kind, idx))
                return out
            pending.pop(pick)
            acc = value
            out.append("ok %s %d %d" % (kind, idx, value))

        elif op == "wait":
            tag = row[1]
            seen = sig_used.get(tag, 0)
            have = sig_at.get(tag, ())
            if seen >= len(have):
                out.append("hold sig %s" % tag)
                return out
            sig_used[tag] = seen + 1
            acc = have[seen]
            out.append("sig %s %d" % (tag, acc))

        elif op == "mark":
            key = row[1]
            seen = ch_used.get(key, 0)
            have = ch_at.get(key, ())
            if seen < len(have):
                ch_used[key] = seen + 1
                acc = have[seen]
            else:
                acc = int(row[2]) if live else 0
            out.append("ver %s %d" % (key, acc))

        elif op == "add":
            acc += int(row[1])
        elif op == "set":
            acc = int(row[1])
        elif op == "jz":
            if acc == 0:
                pc = labels[row[1]]
        elif op == "jnz":
            if acc != 0:
                pc = labels[row[1]]
        elif op == "jmp":
            pc = labels[row[1]]
        elif op == "fin":
            break

    late_row = leftover()
    if late_row is not None:
        out.append(late_row)
        return out
    out.append("fin %d" % acc)
    return out
