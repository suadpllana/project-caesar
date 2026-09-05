# local-B, agent 3

Local probe on candidate B (row transit, belief fact without the arrow): three of three solved it.

The agent's own words only; the brief is not reproduced here (leakcheck must not be circular).

tool calls: 6

## Summary

Rewrote the four policy files under /tmp/claude-0/-home-user-project-caesar/3daf0384-b924-57e9-a314-9b83695689f2/scratchpad/probe/seal/B/a2/pol/ (adm.py, rtn.py, tear.py, emit.py); nothing under lnk/, relay.py or cases/ was touched, and scratch test files were removed afterwards.

What was wrong and what changed:
1. Link permit was never handed back for rows that left us by being dropped or thrown away late. The shipped link ceiling was `took[LINK] + WINL`, so the 117 rows dropped at ticks 11-13 in strand.json held link permit forever and feed 3 was refused every batch. rtn.drained(LINK) is now `bk.ltkn + rows shed` (tear.shed accumulates every late and drop row into st["lost"]), so the link grants 159/198/237 at ticks 11/12/13 and feed 3 lands from tick 19 on (the tick-16 batch is still an over, because it left its producer at tick 13, before the tick-11 grant had arrived).
2. Admission compared against the figure currently standing at the relay (bk.pub). It now compares against what the producer had learned when it sent: rtn keeps a per-level publication history (tick, figure) and adm looks up the latest figure published at a tick <= when - 2*LAG via bisect, falling back to the window (40 feed / 120 link) when nothing qualifies. A reopened feed's history is reset so it starts from 40 known at once.
3. The small-grant test used the book's charge for the feed. It now uses the producer's own count, which is accepted plus refused rows for the current run of that feed (kept in st["cnt"] from adm's own verdicts, reset on reopen). The link's test keeps the relay's own count bk.lsnt.
4. Teardown gap: an arrival on a feed that is down is `late` if `when - bk.shut[fd] < 2*LAG` and the link would not be carried past what the producer had learned (otherwise `over`); from six ticks after the teardown everything is `over`. An arrival on a feed the book has never seen is `over`.
5. Scale: emit.plan no longer walks bk.open() every tick. It evaluates the link every tick, the feeds touched this tick (arrivals including refusals, draws, reopens), and feeds whose idle deadline falls due via a timer wheel (armed at boot for every feed at last+IDLE, and re-armed on every accepted arrival and reopen). Pull is only emitted when the feed is idle. A synthetic wide stream (10,000 feeds, 160,000 ticks, ~146k events) runs in about 1 s.

Checked by hand-walking all three shipped streams and a self-written edge stream (teardown with late/over gap, reopen in the same tick as an arrival, double reopen, draws on empty and gone feeds, unknown feed) line by line against the rules below; every row matched.

## Rules as read

- A ceiling is absolute: finished rows at that level plus the window (40 feed / 120 link), or the floor 12 plus finished for an idle feed.
- Finished for the link = rows drawn plus every row dropped or thrown away late (they left us, so no permit is held); finished for a feed = rows drawn from it in its current run.
- A producer goes by the figure published at the end of tick t from tick t+3; a batch landing at tick W left at W-3, so admission compares against the latest figure published at a tick <= W-6, else the window.
- An arrival is refused (`over`) if it would carry the feed's accepted total past the learned feed figure or the link's accepted total past the learned link figure; neither permit moves on refusal; otherwise it is ok and parked.
- A refused batch still counts as sent in its producer's own tally, and that tally (accepted + refused for the current run) is what the feed's small-grant test measures against.
- A grant is published when value > standing figure (in-flight counts as standing) and either the raise is >= 20 or the standing figure leaves the producer an allowance under 5 while the new figure gives at least 5; nothing else grants, and a figure is never lowered except by the idle pull.
- A feed with nothing accepted for seven ticks (when - last >= 7, last being the last accepted batch or the arm tick) falls to floor + finished, recorded as `pull` when that is below the standing figure.
- A teardown reaches the producer after three ticks; batches landing within six ticks of the teardown are `late` (charged to the link, thrown away, permit freed) unless they would carry the link past the learned link figure, in which case `over`; from the sixth tick on everything from that feed is `over`.
- Tearing down a gone feed and reopening a live feed do nothing; a reopened feed is a fresh run whose totals, refused count and publication history start from nothing and whose producer knows 40 at once while taking the link's figure with the usual lag.
- The link never restarts; its totals and its publication history run across the whole stream.
- Draws on a feed holding nothing or a feed that has gone are quiet; events inside a tick run in stream order and publication happens once at the end of the tick.
- The verdicts, draws, sheds and reopens are the only hooks the policy gets, so the policy tracks touched feeds and idle deadlines itself instead of scanning every open feed each tick.

## Judgment calls

- Which count the link's small-grant test uses: the brief names 'that producer' but the link has no single producer and no producer can see the others, so I used the relay's own link charge (bk.lsnt), not the sum of producers' beliefs including refused rows.
- Exact width of the teardown gap: I treated the teardown like a figure published at the end of its tick (producer learns at T+3, its last batch lands at T+5), so arrivals with when - shut < 6 are late and from T+6 are over; an arrival after the `x` in the same tick is late.
- Whether refused rows count toward the producer's tally when the refusal was for the link rather than the feed: I counted them either way, since the producer cannot tell why it was refused.
- Idle clock origin for a feed that has never accepted anything: I used the book's own `last` (arm tick, 0 for the initial feeds or the reopen tick), so an untouched feed is pulled to 12 at tick 7 and a reopened feed seven ticks after reopening.
- A pull is emitted only when the feed is actually idle; value can only fall below the standing figure through the idle window anyway, so this is a guard rather than a behaviour change, and the link is never pulled.
- An arrival on a feed the book has never armed (not in `feeds`, never reopened) is treated as `over`, since the book has no shut tick for it; a reopen of such a feed arms it normally.
- The initial window (40 / 120) is treated as known by the producer at once rather than as a figure published at tick 0 with a three-tick lag; the two readings agree in every stream I could construct because nothing else can be learned before tick 6.
- The state kept in `st` is my own (publication history, refused counts, touched set, timer wheel, shed total); I dropped the shipped `took`/`lost` tallies because the book already holds drawn totals and the shed total is only needed for the link.
