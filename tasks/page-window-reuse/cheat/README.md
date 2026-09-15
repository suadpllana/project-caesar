# Cheat attempts

Thirty-seven whole submissions, each scoring 0, in four families. Every one is the reference
with one thing changed, so a zero means the change was caught rather than that the script failed
to apply; `authoring/page-window-reuse/emit.py` builds them and asserts each substitution fired
and each emitted file parses.

**Wrong readings (25).** One plausible misreading of one stated rule each: residency without the
sink or with the window measured from the prompt, a fill that lets its middle go as it writes, a
walk that carries on past a page that is gone or refuses a page somebody else holds, a released
page kept as reusable when no walk can reach it, a take-back that takes the lowest numbered page
or the newest release or leaves what is below it alone or refuses a page with something under it,
a pool that preempts before it takes a page back, a preemption that takes the oldest resident
request or carries on with the step or keeps the work it discarded, a chunk that stops mid page,
a queue that jumps, a step that fills before it decodes, a walk charged to the budget, a page
that keeps its own memory when the same tokens already sit below the same page, and pages
released in reverse order of their tokens. `authoring/page-window-reuse/cheat_report.py` names
the enumerated program that catches each.

**Correct and too slow (3).** Residency recomputed over every page of a request on each token,
the oldest release found by scanning the reusable pages, and the reach of a take-back found by
sweeping the page table. All three print exactly the reference's traces and take 110, 144 and 203
seconds against a 60 second limit.

**The answer key (1).** `cheat-forge-from-truth.sh` carries `tests/seal/gt.json` verbatim and
replays it. It reproduces all 32 enumerated programs and none of the 396 generated after the
agent's container is gone.

**Isolation probes (8).** The verifier runs the submitted service, so these are mandatory
(`docs/VERIFIER-ISOLATION.md`): reading the sealed model and frozen answers, a double forked
process writing the reward after grading, a uid and write probe against the verifier's own paths,
a planted report, a report planted and the worker exited clean before it could be overwritten,
a record that is not a list of lines, a rewrite of the seed and size of its own exam, and a
rewrite of the parts of the tree the verifier does not take. Each sits on top of a pool that
cannot be right, so a reward of 1 could only come from the attack.
