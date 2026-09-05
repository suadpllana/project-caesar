# local-B, agent 2

Local probe on candidate B (row transit, belief fact without the arrow): three of three solved it.

The agent's own words only; the brief is not reproduced here (leakcheck must not be circular).

tool calls: 6

## Summary

Rewrote the four policy files in place (pol/adm.py, pol/rtn.py, pol/tear.py, pol/emit.py); nothing under lnk/, relay.py or cases/ was touched.

What was wrong and what changed:
- Link permit was never handed back for rows that left the relay by teardown or as late arrivals: rtn.drained(LINK) counted only drawn rows. Now the link ceiling is drawn rows + every shed row (drops and lates) + 120, so strand.json publishes link grants 159/198/237 at ticks 11-13 and feed 3 gets through from tick 19.
- Admission compared against the standing figure (bk.pub) instead of what the producer had learned when it sent the batch. adm.verdict now keeps a per-level publication history (rtn.learned) and holds an arrival at tick T to the latest figure published at the end of a tick <= T-6 (three ticks out, three ticks back), or the window if none; a reopened feed starts from the window at once and forgets the old run's history.
- The shipped policy had no late path. Arrivals on a torn-down feed within the six-tick gap (T - shut_tick < 6) are 'late' unless they would carry the link past its learned figure, in which case 'over'; from the sixth tick on everything is 'over'.
- The small-grant test used the book's charge; it now uses the producer's own count for a feed (accepted rows + every refused row of that run, kept by adm from its own verdicts and reset on reopen) and the relay's own link count (bk.lsnt) for the link.
- emit.plan walked every open feed every tick (bk.open() sorts all feeds), which cannot fit a 10k-feed / 150k-tick stream in the budget. It now examines only levels touched this tick (dirty set fed by the verdict, draw, shed and reopen hooks) plus feeds whose idle deadline (last accept + 7) falls on this tick, booked in a tick-keyed bucket at arm/accept/reopen time, including the deadline at tick 7 for every feed armed at the start. Fuzzed against a naive every-level sweep of the same rules: 0 mismatches over 4000 random streams; a 10.5k-feed, 160k-tick stream runs in 0.8 s.

Outputs on the shipped streams: strand now lands feed 3 from tick 19 with link grants after each drop (over only at 16 and 22, where the producer was still on old figures); lull gains an over at 24 (sent on the floor figure 42) and a pull at 27; handover is unchanged.

## Rules as read

- A ceiling is absolute: rows the level has finished with (drawn, or thrown away by drop/late for the link) plus the window (40 feed, 120 link, or the 12 floor when the feed is idle).
- A feed's finished count is its current run's drawn rows (bk.tkn); the link's is bk.ltkn plus every row shed by drop or late, across the whole stream, so no row still holds link permit after it has left.
- A grant is published at tick end exactly when the new ceiling exceeds the standing figure by 20 or more, or when the standing figure would leave the producer unable to send 5 rows while the new one lets it (standing figure = bk.pub, which counts figures still in flight).
- A figure is never published unless it is above the standing one, except the idle pull, which lowers a feed to drawn + 12.
- Idle: a feed with nothing accepted (no stow) for 7 ticks, measured from bk.last (last accept or arm time), is at the floor from tick last+7 until its next accepted batch; the pull is recorded when the floor ceiling is below the standing figure.
- A producer learns a figure published at the end of tick t from tick t+3, and a batch landing at T was sent at T-3, so an arrival at T is judged against the latest figure published at the end of a tick <= T-6, else the window.
- An arrival on a live feed is refused ('over', nothing moves) if it would carry the feed's charge past the feed's learned figure or the link's charge past the link's learned figure; otherwise 'ok' and parked.
- A refused batch counts as sent in its producer's eyes: the feed's small-grant test uses accepted + refused rows for the current run; the link's uses the relay's own count bk.lsnt, since no producer can see the link.
- Teardown throws parked rows away (one drop) and the producer sends on for three ticks: arrivals on a shut feed with T - shut < 6 are 'late' (billed to the link, shed, thrown away) unless they would carry the link past its learned figure ('over'); from T - shut >= 6 every arrival is 'over'.
- Tearing down a gone feed and reopening a live one do nothing; a reopened feed is a fresh run: counts, refused rows and publication history start again, it knows the 40 window at once, and it goes by the link's history like everyone else; the link never restarts.
- Draws against nothing, and draws or events on unknown feeds, are quiet; a feed shut with nothing parked emits nothing.
- Events inside a tick apply in stream order; publication happens once at tick end, one row per level, and the machine sorts them.

## Judgment calls

- Effective admission lag is six ticks (three to learn, three for the batch to land): an arrival at T is held to the latest figure published at end of tick <= T-6. The brief's 'left its producer three ticks before' plus 'goes by from the third tick after' make this the literal reading; a three-tick reading would have made the second sentence pointless.
- Late window is T - shut_tick <= 5 (producer learns at shut+3, its last batch leaves at shut+2 and lands at shut+5); an arrival in the same tick after the teardown is late; from shut+6 it is over.
- Small-grant 'spent' for a feed = accepted rows + refused rows of the current run (per 'a batch we turn away is sent as far as its producer knows'); for the link = bk.lsnt, the relay's own count, because no producer can see the link total. Refused rows on a shut feed are not tracked (no feed ceiling exists).
- Idle is measured from bk.last as the machine keeps it, which includes the arm time: a feed nobody touches pulls to 12 at tick 7 (and a reopened one at reopen+7); the shipped '>= IDLE' test was kept.
- Levels are examined only when something about them changed this tick (verdict on a live feed, ok/late arrival for the link, draw, shed, reopen) or on the feed's idle deadline; I verified this is exactly equivalent to examining every open level every tick by fuzzing both against each other.
- The general rule was applied uniformly at the idle deadline: a pull only when the floor ceiling is below the standing figure; if drawn+12 is not below, the ordinary grant tests apply (the fuzz found this never produces a grant that the rules would not otherwise produce).
- Arrivals for a feed the plan never listed are treated as over, and a teardown at tick 0 is distinguished from an unknown feed by membership in bk.shut rather than by the shut value.
