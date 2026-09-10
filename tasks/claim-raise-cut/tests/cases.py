"""Enumerated programs, one per graded decision plus the must-still-work side of each
fence. The name of a case is the reading it separates; `readings` in the authoring set
asserts that each of these actually catches the reading it is named for.
"""

CASES = [
    # An ordinary run: compatible claims, a pop, two ends, and nothing cut. A service
    # that has turned conservative fails here before it reaches anything subtle.
    ("plain-flow", """
        take t1 k1 scan
        take t2 k1 grow
        take t3 k1 scan
        take t1 k2 pin
        take t2 k2 edit
        drop t1 k1
        end t2
        end t1
        end t3
    """),
    # Rule 2: join(scan, pin) is edit, which no rank over the five marks produces.
    ("join-pair", """
        take t1 ka scan
        take t2 ka scan
        take t1 ka pin
    """),
    # Rule 2 again, the other pair a rank gets wrong: join(edit, grow) is seal.
    ("join-cross", """
        take t1 ka edit
        take t2 ka pin
        take t1 ka grow
    """),
    # Rule 3: the only holder raises and is not tested against itself.
    ("self-alone", """
        take t1 ka scan
        take t1 ka edit
        end t1
    """),
    # Rule 3 with company: the raise stands beside the other holder, and would not stand
    # beside an aggregate that folded the raiser's own claim in.
    ("self-mate", """
        take t1 ka scan
        take t2 ka pin
        take t1 ka scan
    """),
    # Rule 4: raises are served in the order their claimants came to hold the item, and
    # here that is the reverse of the order they asked in.
    ("raise-order", """
        take t1 ka pin
        take t2 ka pin
        take t3 ka edit
        take t2 ka scan
        take t1 ka scan
        drop t3 ka
    """),
    # Rule 4: a raise that cannot be granted is passed over, not a barrier to later ones.
    ("raise-pass", """
        take t1 ka scan
        take t2 ka scan
        take t3 ka scan
        take t1 ka pin
        take t2 ka grow
    """),
    # Rule 4: the pin. Nothing held excludes t3's scan, and it still waits.
    ("pin-fresh", """
        take t1 ka scan
        take t2 ka scan
        take t1 ka pin
        take t3 ka scan
    """),
    # The pin lifts when the raise goes through, and the pop puts the mark back.
    ("pin-lift", """
        take t1 ka scan
        take t2 ka scan
        take t1 ka pin
        take t3 ka scan
        drop t2 ka
        drop t1 ka
    """),
    # Rule 4: the fresh walk stops at the first request it cannot grant, even though the
    # one behind it would stand with everything held.
    ("queue-stop", """
        take t1 ka pin
        take t2 ka grow
        take t3 ka scan
    """),
    # Rule 6: the ring the conflict reading cannot see. t3 asks for scan and the only
    # claims on ka are scans, so no holder excludes it, yet it waits for t1.
    ("edge-miss", """
        take t1 ka scan
        take t2 ka scan
        take t3 kb edit
        take t2 kb scan
        take t1 ka pin
        take t3 ka scan
    """),
    # Rule 6 the other way: t1 holds a mark that excludes what t3 asked for, and t3 does
    # not wait for it, because taking t1 away lets the stuck raise through instead.
    ("edge-phantom", """
        take t3 kb edit
        take t1 ka edit
        take t2 ka pin
        take t2 ka grow
        take t1 kb scan
        take t3 ka scan
    """),
    # Rule 6: three holders of one mark, two of them raising. No single departure grants
    # either raise, so there is no ring and nothing is cut.
    ("edge-share", """
        take t1 ka scan
        take t2 ka scan
        take t3 ka scan
        take t1 ka pin
        take t2 ka pin
    """),
    # Rule 7: the cut takes the transaction holding claims on the fewest items.
    ("cut-fewest", """
        take t1 ka scan
        take t1 kb scan
        take t1 kc scan
        take t2 ka scan
        take t1 ka edit
        take t2 ka edit
    """),
    # Rule 7: with the same count on both sides, the later request goes.
    ("cut-late", """
        take t1 ka scan
        take t2 ka scan
        take t1 ka edit
        take t2 ka edit
    """),
    # Rule 7: one step leaves two rings, and the service cuts until neither is left.
    ("cut-again", """
        take t2 kb scan
        take t3 kb scan
        take t4 kc scan
        take t5 kc scan
        take t1 ka seal
        take t2 ka scan
        take t2 kb edit
        take t3 ka scan
        take t3 kb edit
        take t4 ka scan
        take t4 kc edit
        take t5 ka scan
        take t5 kc edit
        end t1
    """),
    # Rule 8: the item the victim was waiting on is swept too, so the request queued
    # behind the cancelled one goes through.
    ("cut-wake", """
        take t5 kx pin
        take t5 kz scan
        take t2 ky scan
        take t2 kx grow
        take t4 kx scan
        take t5 ky edit
    """),
    # Rule 5: a drop takes one mark off, not the whole stack.
    ("drop-pop", """
        take t1 ka scan
        take t1 ka pin
        take t2 ka scan
        drop t1 ka
    """),
    # Rule 5 with a deeper stack: what is left after each pop is the join of the rest.
    ("drop-mark", """
        take t1 ka pin
        take t1 ka scan
        take t1 ka grow
        drop t1 ka
        drop t1 ka
        take t2 ka edit
    """),
    # Rule 10: an ending transaction's items are swept in the order it came to hold them,
    # which here is not the order of their names.
    ("shed-order", """
        take t1 kb scan
        take t1 ka scan
        take t2 ka edit
        take t3 kb edit
        end t1
    """),
    # Rule 9: two transactions granted by one release resume in grant order, each running
    # its own backlog out before the next one starts.
    ("resume-order", """
        take t1 ka seal
        take t2 ka scan
        take t3 ka scan
        take t2 kb scan
        take t3 kb scan
        end t1
    """),
    # Rule 9 with a longer backlog behind each grant.
    ("resume-run", """
        take t1 ka seal
        take t2 ka scan
        take t3 ka scan
        take t2 kb scan
        take t2 kc scan
        take t3 kb scan
        end t1
    """),
    # Rules 8 and 10: a finished transaction is named again and nothing happens.
    ("gone-ignore", """
        take t1 ka scan
        end t1
        take t1 ka seal
        take t2 ka edit
        end t2
    """),
    # Rule 7 across rings: two appear in the same step and the transactions on them hold
    # different numbers of items, so the cut has to compare across both rather than take
    # the first ring it happens to find.
    ("ring-pair", """
        take t4 r1 scan
        take t5 r1 scan
        take t6 r2 scan
        take t7 r2 scan
        take t1 gate seal
        take t4 gate scan
        take t7 gate scan
        take t7 r2 edit
        take t4 r1 edit
        take t5 r1 edit
        take t6 r2 edit
        end t1
    """),
    # Rule 4 with a returning holder: an item dropped to nothing and taken again is held
    # from that moment, so the raise order is not the order the names first appeared.
    ("again-life", """
        take t3 ka edit
        take t1 ka pin
        take t2 ka pin
        drop t1 ka
        take t1 ka pin
        take t1 ka scan
        take t2 ka scan
        drop t3 ka
    """),
]


def steps(text):
    out = []
    for line in text.strip().splitlines():
        line = line.strip()
        if line:
            out.append(tuple(line.split()))
    return out


def programs():
    return [(name, steps(body)) for name, body in CASES]
