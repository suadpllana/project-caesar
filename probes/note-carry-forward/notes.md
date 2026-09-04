# note-carry-forward, easiness probe, 2026-09-04 (the two-decision version)

Three trajectories, agents' own words only. All three solved it in about
seventy-five seconds against a 14400 s budget: read the tree, one
`cat > note/rule.py`, one `cat > note/board.py`, both correct first time, no
intermediate wrong version in any of them.

## Attribution

- `leakcheck`: nothing above the floor on any of the three. Not the wording.
- The shipped `note/rule.py` carried `from scr import pin` and never used it,
  and `grp.spans` was called by nothing while the brief named both modules.
  All three agents wrote that back in their own summaries. **Mode B**, and
  `preflight` had warned about it.
- Beyond the arrows, the mechanism was two decisions in 98 lines. The quality
  review said the same thing twice, in different words, and was right both
  times.

## What the bundle looks like now

Threads carry spans rather than a line, have states that replies and
resolutions move them through, and merge by overlap to a fixed point. Twelve
decisions are graded where two were, four of them need history no single
revision supplies. These three submissions all fail the current bundle: every
one is level-triggered, none carries a span, and none has a merge pass at all.

**Not re-probed since the rebuild.** That is the first thing to do.
