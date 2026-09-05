# local-cur, agent 1

Local calibration probe on the round-three version (the one the pipeline solved 3 of 3): two of four agents ran before the account limit; both solved it.

The agent's own words only; the brief is not reproduced here (leakcheck must not be circular).

tool calls: 7

## Summary

Rewrote /tmp/claude-0/-home-user-project-caesar/3daf0384-b924-57e9-a314-9b83695689f2/scratchpad/probe/seal/cur/a1/pol/{adm,rtn,tear,emit}.py in place; nothing else in the tree was touched (lnk/, relay.py, cases/ untouched; my scratch dir and __pycache__ removed afterwards).

What was wrong in the shipped tree and what changed:
1. Link permit was never handed back for rows that left us by being thrown away. rtn.drained(LINK) counted only drawn rows, so the 117 rows dropped on strand's three teardowns stayed charged forever and feed 3 could never land a batch. Now finished(link) = bk.ltkn + every row shed (drops and late rows, cumulative for the whole stream, never reset by a reopen); finished(feed) = bk.tkn[fd] for the current run. Strand now grants the link 159/198/237 on ticks 11-13 and feed 3's 12-row batches land from tick 16.
2. Admission compared against bk.pub, the figure just published, not the figure the producer has learned. rtn.known() keeps a per-level queue of (publish tick, figure) and advances a learned figure once tick+3 <= now; default is the window (40 feed / 120 link); a reopened feed's queue is discarded and its learned figure reset to 40 at once.
3. No 'late' verdict existed: a torn-down feed's arrivals were all 'over'. adm.verdict now returns 'late' for arrivals within [shut tick, shut tick+2] unless the link test refuses them ('over'), and 'over' after that window.
4. The small-grant test used the book's charge for feeds; the brief says a refused batch is still sent as far as the producer knows, so the feed test now uses snt[fd] + refused rows this run (kept by the policy from its own 'over' verdicts, reset on reopen); the link test uses bk.lsnt, our own count.
5. emit.plan scanned every open feed every tick (bk.open() sorts all feeds), which is hopeless on a 10k-feed / 150k-tick stream. It is now event-driven: levels touched during the tick (ok arrival -> feed+link; over on a live feed -> feed; draw -> feed+link; shed -> link; reopen -> feed) plus feeds whose idle deadline (last acceptance or arm tick + 7) is due, from a lazy heap; the stale entries are re-checked against bk.last and skipped. A 10000-feed, 160000-tick, 300k-event stream runs in 2.6 s.
6. Pull only ever lowers a feed (never the link) and only when the idle test holds; grant only when value > standing and (raise >= 20 or the small-grant rule).

Verification: the three shipped streams (strand now: pull 7 3 12; drops 11/12/13 each followed by a link grant; feed 3 grants 40,64,88,...; park 3 0; handover and lull unchanged from the shipped output, which was already right there). An independent naive model (full per-tick scan, history scan for learned figures, no lnk/ code) agreed with the relay on 800 random streams (1-30 feeds, 20-600 ticks, small and large batches, same-tick x/o/a mixes) covering 34k overs, 11k grants, 8.7k pulls, 2.2k lates, 2.7k drops. Five hand-derived corner streams (late window incl. over-in-window and after-window, small grant triggered by an over, small grant triggered by an ok arrival on the link, reopen forgetting an in-flight grant with x+o+a in one tick, pull then sub-threshold draws then re-grant on acceptance then second pull) matched paper expectations exactly.

## Rules as read

- A ceiling is an absolute running total: finished rows at that level plus the window (40 feed, 120 link); rows that have left us (drawn, dropped at teardown, thrown away as late) release permit at every level they were charged to, so finished(link) = drawn + dropped + late, cumulative for the stream; finished(feed) = drawn in the current run.
- A producer goes by a figure only from the third tick after the tick it was published at; until anything has been published to a level it goes by the window; a reopened feed's producer knows the feed window at once and figures published to the old run (in flight or not) are forgotten.
- The link's learned figure is one thing shared by every producer with the same three-tick lag; the link never restarts and its totals (charged, drawn, lost) carry across teardowns and reopens.
- A grant is published exactly when value > standing and either the raise (value minus the last published figure, in-flight figures included) is at least 20, or the small-grant rule holds: standing - spent < 5 and value - spent >= 5.
- For the small-grant rule, spent for a feed is the producer's count: the book's charge plus every batch of that run we turned away with 'over'; spent for the link is our own count, bk.lsnt (charged ok rows plus billed late rows), refused rows excluded.
- Nothing else earns a grant, and a figure that is not above the standing one is never published, except the idle fallback.
- Idle fallback: a feed with nothing accepted for seven ticks (now - bk.last >= 7, bk.last being the arm tick or last accepted arrival) has window 12 instead of 40; its value is drawn + 12, and when that is below the standing figure it is published as a 'pull'; only feeds, never the link.
- An arrival on a live feed is refused ('over') if charge-so-far + rows would pass the learned figure at either level (strictly greater refuses, equal is ok); neither permit moves, nothing is parked; otherwise 'ok' and parked, charged to both permits.
- An arrival on a feed torn down at tick S, landing at tick S, S+1 or S+2, is 'late' (charged to the link, thrown away, link permit released) unless the link test refuses it, in which case it is 'over'; from S+3 on everything from that feed is 'over'.
- Draws take whole batches in landing order and free the rows at both levels; a draw on an empty or gone feed is quiet; tearing down a gone feed or reopening a live feed does nothing; a teardown with rows parked drops them all in one 'drop' and those rows release link permit.
- A reopened feed is a fresh run: charge, drawn, refused count and idle clock start again, standing figure and learned figure are the feed window.
- Events in a tick happen in stream order, publication happens once at the end of the tick from the state as it then stands, and the machine sorts the rows, so the policy hands back at most one row per level per tick.

## Judgment calls

- Idle clock runs from the arm tick as well as from the last acceptance, because the frozen book sets bk.last on arm exactly like on stow: a feed that never accepts anything is pulled to 12 at the end of tick 7 (tick 7 after a reopen at tick 0 likewise). Chosen; the alternative (clock starts only after a first acceptance) was rejected because it would leave bk.last's arm value with no purpose.
- Seven ticks means now - last >= 7 (pull at the end of tick last+7), not > 7.
- Late rows count as rows that have left us, so they release link permit the same tick they are billed (net effect: the link ceiling rises by that many rows). Chosen from 'thrown away' plus 'no row may still be holding permit once it has left us'.
- Refused ('over') batches on a live feed count toward that feed's producer count for the small-grant rule regardless of which level refused them; overs on a gone feed count nowhere; late rows count toward nothing at feed level.
- The threshold and the never-lower rule are both measured against the last published figure including in-flight ones (bk.pub), the same reference the brief names for the small-grant test.
- Value equal to the standing figure publishes nothing (neither grant nor pull).
- A pull is issued only for a feed and only while the idle test holds; the link is never pulled (its value cannot fall).
- The link's learned figure is global: a reopened feed's new producer goes by the same link figure as everyone else, with no reset, since only the feed's own published figures are said to be forgotten.
- An arrival for a feed id the book has never armed is treated as 'over' (not in the streams, guarded anyway).
- Rows refused because of the link on a live feed touch only that feed's small-grant test (the link's own count does not move), so the link is not re-examined on an over.
