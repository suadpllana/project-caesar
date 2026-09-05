"""Plausible misreadings of the rules, each written as the reference with one
decision made the other way.

Two things are measured here. Every reading must move a real share of the
generated streams - a reading that moves a handful is a lottery ticket rather
than a decision, and it is either dropped or the generator is tuned until the
state it turns on is common. And every reading must be separated by the
enumerated set, so a wrong answer names the rule instead of surfacing as a
count of random streams.

Every reading keeps the reference's schedule, so it is caught by the rule it
gets wrong and never by the resource gate; the two readings that give the
schedule up live in emit.py as the slow cheats.
"""

DRAIN_TAKEN_ONLY = ('rtn.py', 'def drained(', None, '''def drained(st, bk, level):
    if level == LINK:
        return bk.ltkn
    return bk.tkn.get(level, 0)
''')

FEED_DRAIN_SHED = ('rtn.py', 'def drained(', None, '''def drained(st, bk, level):
    if level == LINK:
        return bk.ltkn + st.get("gone", 0)
    return bk.tkn.get(level, 0) + st.get("gone", 0)
''')

OWE_FROM_LEARNED = ('emit.py', 'def owed(', '\n\n\ndef plan(', '''def owed(st, bk, when, level, value):
    if level == LINK:
        spent, dflt = bk.lsnt, WINL
    else:
        spent, dflt = bk.snt.get(level, 0), WINF
    return tear.seen(st, when, level, dflt) - spent < MINB and value - spent >= MINB
''')

OWE_IGNORES_FREE = ('emit.py', 'def owed(', '\n\n\ndef plan(', '''def owed(st, bk, when, level, value):
    spent = bk.lsnt if level == LINK else bk.snt.get(level, 0)
    return bk.pub.get(level, 0) - spent < MINB
''')

THR_ON_SPENT = ('emit.py', '    for level in sorted(look):', '    st["dirty"] = set()', '''    for level in sorted(look):
        seat = bk.pub.get(level)
        if seat is None:
            continue
        value = ceiling(st, bk, when, level)
        spent = bk.lsnt if level == LINK else bk.snt.get(level, 0)
        if value > seat:
            if value - spent >= THR or owed(st, bk, when, level, value):
                out.append((level, "grant", value))
        elif value < seat:
            out.append((level, "pull", value))
''')

EMIT_DEAD_FEEDS = ('emit.py', '    for level in sorted(look):', '    st["dirty"] = set()', '''    for level in sorted(look):
        seat = bk.pub.get(level, 0)
        value = ceiling(st, bk, when, level)
        if value > seat:
            if value - seat >= THR or owed(st, bk, when, level, value):
                out.append((level, "grant", value))
        elif value < seat:
            out.append((level, "pull", value))
''')

PULL_AS_DELTA = ('emit.py', '    for level in sorted(look):', '    st["dirty"] = set()', '''    for level in sorted(look):
        seat = bk.pub.get(level)
        if seat is None:
            continue
        value = ceiling(st, bk, when, level)
        if value > seat:
            if value - seat >= THR or owed(st, bk, when, level, value):
                out.append((level, "grant", value))
        elif value < seat:
            out.append((level, "pull", seat - value))
''')

NO_LATE_WINDOW = ('adm.py', 'def verdict(', None, '''def verdict(st, bk, when, fd, rows):
    if not bk.up(fd):
        return "over"
    if bk.snt[fd] + rows > tear.seen(st, when, fd, WINF):
        return "over"
    if bk.lsnt + rows > tear.seen(st, when, LINK, WINL):
        return "over"
    tear.touch(st, fd)
    tear.touch(st, LINK)
    tear.due(st, fd, when + IDLE)
    return "ok"
''')

JUDGE_ON_HELD = ('adm.py', 'def verdict(', None, '''def verdict(st, bk, when, fd, rows):
    room = bk.pub.get(LINK, 0)
    if not bk.up(fd):
        shut = bk.shut.get(fd)
        if shut is not None and when - shut < LAG:
            if bk.lsnt + rows > room:
                return "over"
            return "late"
        return "over"
    if bk.snt[fd] + rows > bk.pub.get(fd, 0):
        return "over"
    if bk.lsnt + rows > room:
        return "over"
    tear.touch(st, fd)
    tear.touch(st, LINK)
    tear.due(st, fd, when + IDLE)
    return "ok"
''')

LATE_NOT_SHED = ('tear.py', 'def shed(', '\n\n\ndef opened(', '''def shed(st, bk, when, fd, rows):
    if bk.shut.get(fd) == when:
        st["gone"] = st.get("gone", 0) + rows
    touch(st, -1)
''')

KEEP_SAID_ON_REOPEN = ('tear.py', 'def opened(', '\n\n\ndef window(', '''def opened(st, bk, when, fd):
    touch(st, fd)
    due(st, fd, when + IDLE)
''')

READINGS = {
    "drain-taken-only": [DRAIN_TAKEN_ONLY],
    "feed-drain-shed": [FEED_DRAIN_SHED],
    "owe-from-learned": [OWE_FROM_LEARNED],
    "owe-ignores-free": [OWE_IGNORES_FREE],
    "thr-on-spent": [THR_ON_SPENT],
    "emit-dead-feeds": [EMIT_DEAD_FEEDS],
    "pull-as-delta": [PULL_AS_DELTA],
    "no-late-window": [NO_LATE_WINDOW],
    "judge-on-held": [JUDGE_ON_HELD],
    "late-not-shed": [LATE_NOT_SHED],
    "keep-said-on-reopen": [KEEP_SAID_ON_REOPEN],
}
