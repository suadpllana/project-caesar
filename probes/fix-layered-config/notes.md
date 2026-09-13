What the easiness probe of 13 September 2026 measured, and what was done about it.

Three trials against the bundle imported as the first commit of this task on the branch. Two
solved it. The three transcripts are beside this file with the brief stripped from the top of
each, so that `tools/leakcheck.py` compares the solver's words against the brief rather than
the brief against itself. The transcripts carry no verdicts: which of the three failed, and on
what, cannot be read from them.

What all three have in common is the shape of the first substantive message. Each read the
six editable files and the frozen tree once, ran the shipped plans, and then listed every
defect of the shipped service against the sentence of the brief it violated - the count of
interior paths, `ask` at the final view, guards read mid-layer, `mix` neither clearing nor
keeping the writing layer, `old` read at the writing layer's number, the right side first,
`pick` by subtree, `map` never run. None of them ran an experiment before committing to the
plan. All three then wrote the six files in one pass around the same design: an immutable trie
with a count on every node, a `mix` that shares the source's node, a `map` that wraps that node
with a lazy path rewrite, values remembered by definition and view. The design the task rested
on was each agent's first idea, and it was right.

`tools/leakcheck.py` finds nothing above the floor in any of the three. The plan did not come
from quoted prose. It came from the rules being individually implementable and the structures
each rule wants being the standard ones.

What differed was the checking. Trial 2 wrote a brute-force model of the brief and fuzzed
1,900 random plans against its service; trial 1 wrote hand plans of its own; trial 3 ran the
shipped plans and one synthetic doubling plan and stopped. Under a contract whose fast
structures were the obvious ones, that difference in checking is the only place the three could
have parted, and the transcripts do not say whether it was.

The repair is recorded in tasks/fix-layered-config/STATE.md under "Easiness recovery -
2026-09-13 (probe 2 of 3)": a live window, `tie`, whose stated rules are simple and whose
consequences invalidate the stored count, the shared copy, the node-keyed lazy wrapper and the
prefix-settled lookup at once.
