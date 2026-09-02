"""A second reading of the round rules, written from the specification.

This shares no code with the tree under test. It never imports `house`, it holds
obligations as plain tuples in plain lists rather than as objects in a Book, and it
reaches the round's settlement by shrinking a SET of chosen obligations rather than by
lowering a depth per party. The two arrive at the same place because the rules say so,
and the point of writing it twice is that a disagreement means one of them has read the
rules wrong rather than that a run went badly.

The rules it implements, in the order they matter:

  * A party pays out of what it holds plus what reaches it in the same round. The round
    is one motion, so a ring of parties who owe each other and hold nothing clears.
  * A party's obligations sit in the order the house wrote them down, and a round takes
    them from the front of that line, never one before the one in front of it.
  * A round may only reach an obligation whose day has come, and the line stops at the
    first obligation whose day has not, whatever sits behind it.
  * No party ends a round holding less than nothing.
  * A round leaves nothing on the table.
  * Anything the round could reach and did not move is given up on, oldest first, one
    at a time, because taking one out of a line is what lets the round reach what was
    behind it.

The settlement is the largest choice that stands up. Shrinking from the top reaches it:
the loop only ever drops the last chosen obligation of a party that is short even with
everything the current choice sends it, and no choice that stands up contains that
obligation while the party is short.
"""


def _read(text):
    who = []
    run = 0
    rows = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        f = ln.split()
        if f[0] == "who":
            who = f[1:]
        elif f[0] == "run":
            run = int(f[1])
        elif f[1] == "fund":
            rows.append((int(f[0]), "fund", f[2], int(f[3])))
        else:
            rows.append((int(f[0]), "owe", f[2], f[3], f[4], int(f[5]), int(f[6])))
    return who, run, rows


def _settle(hold, lines, obs, reach):
    """Return, per party, how many from the front of its line the round moves."""
    take = {n: list(range(reach[n])) for n in lines}
    while True:
        got = {n: 0 for n in lines}
        for n in lines:
            for k in take[n]:
                got[obs[lines[n][k]][1]] += obs[lines[n][k]][2]
        short = []
        for n in lines:
            spend = sum(obs[lines[n][k]][2] for k in take[n])
            if hold[n] + got[n] - spend < 0:
                short.append(n)
        if not short:
            return {n: len(take[n]) for n in lines}
        short.sort()
        take[short[0]].pop()


def play(text):
    who, run, rows = _read(text)
    hold = dict((n, 0) for n in who)
    lines = dict((n, []) for n in who)
    obs = {}
    seq = {}
    fate = {}
    log = []
    made = 0
    for t in range(1, run + 1):
        for r in rows:
            if r[0] != t:
                continue
            if r[1] == "fund":
                hold[r[2]] += r[3]
            else:
                obs[r[2]] = (r[3], r[4], r[5], r[6])
                seq[r[2]] = made
                made += 1
                fate[r[2]] = ("open", -1)
                lines[r[3]].append(r[2])
        while True:
            reach = {}
            for n in who:
                k = 0
                for i in lines[n]:
                    if obs[i][3] > t:
                        break
                    k += 1
                reach[n] = k
            deep = _settle(hold, lines, obs, reach)
            moved = []
            for n in who:
                for i in lines[n][: deep[n]]:
                    moved.append(i)
            for i in moved:
                pr, pe, am, _ = obs[i]
                hold[pr] -= am
                hold[pe] += am
                fate[i] = ("paid", t)
                log.append(("paid", i, t))
            for n in who:
                lines[n] = lines[n][deep[n]:]
            over = []
            for n in who:
                k = 0
                for i in lines[n]:
                    if obs[i][3] > t:
                        break
                    k += 1
                over.extend(lines[n][:k])
            if not over:
                break
            over.sort(key=lambda i: seq[i])
            gone = over[0]
            fate[gone] = ("gone", t)
            log.append(("gone", gone, t))
            lines[obs[gone][0]] = [i for i in lines[obs[gone][0]] if i != gone]
        for n in who:
            log.append(("hold", n, hold[n]))
    return {"log": log, "sheet": dict((i, fate[i]) for i in sorted(fate))}


def rounds(rows):
    """Split a record into rounds, and settle what inside one is ordered and what is not.

    A round records what it moved, what it gave up on, and what every member held when it
    closed. WHICH obligations moved is forced by the rules; the order they are written in
    within one round is not, because a submission may hand the book its round in one motion or
    in several and arrive at the same round either way. The giving-up is ordered, since oldest
    first is a rule, so that sequence is kept exactly. Grading the moved rows as a sequence
    would fail a correct implementation for choosing to split a call, which is what the
    reward-hacking audit means by grading an arrangement of the code.
    """
    out = []
    paid, gone, hold = [], [], []
    for r in rows:
        if r[0] == "hold":
            hold.append(list(r))
            continue
        if hold:
            out.append([sorted(paid), gone, hold])
            paid, gone, hold = [], [], []
        (paid if r[0] == "paid" else gone).append(list(r))
    if paid or gone or hold:
        out.append([sorted(paid), gone, hold])
    return out
