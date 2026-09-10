What the easiness probe of 10 September 2026 measured, and what was done about it.

Three trials against the bundle the contributor uploaded on 2026-09-10 (span-claim-charge,
no STATE.md shipped). Two solved it. The three transcripts are beside this file with the brief
stripped from the top of each, so that `tools/leakcheck.py` compares the solver's words
against the brief rather than the brief against itself. The transcripts carry no verdicts, but
the traces they printed do: trial 1 printed `g a,b rel=10` on `pair.txt` and on `weave.txt`,
where the reference prints 12 and 16, and trials 2 and 3 printed the reference's numbers on
every shipped program. Trial 1 read the freed-by-dropping rule for a set as the spans every
named line stands on. That is a reading slip on one rule, and it is the failure.

What all three have in common is the first substantive message. Each read the five store
modules, the frozen driver and the shipped programs in two or three tool calls, ran
`tiny.txt`, and listed every defect of the shipped store against the sentence of the brief it
violated: the span-level in-place test, first-fit allocation without the largest-run fallback,
a free map that merges forward only, blocks taken before the replaced claims are released,
charges added up from claim widths and recounted per query, a drop that gives nothing back.
None ran an experiment before committing. All three then wrote the five files in one or two
heredocs, timed `wide.txt` and `churn.txt` once, and were done in seven to nine tool calls.

Where the plan came from, in order of weight:

  1. the tree - the shipped `hold.py` already carried the two indexes per span (`on`, the
     claims; `by`, a count per line), `tally.py` already carried the spans per line and the
     gain/lose hooks, `item.py` already carried the cut/pull/lay/holes/sole skeleton. The
     reference is about a hundred lines of diff away from the shipped store, and every agent
     kept the structure and repaired the functions;
  2. the brief - it narrates the write path in execution order and refutes the count reading
     in as many words. `tools/leakcheck.py` finds trial 1 reusing "so a write can land on the
     ground it just freed", "is judged against the free total" and "whole standing set lies
     inside", and trial 2 reusing "is judged against the free total that release produces"
     and "a free run on either side"; trial 3 is below the floor.

Neither solver flagged a judgement call; the population had exercised every rule they read.

The repair is recorded in tasks/span-claim-charge/STATE.md under "Easiness recovery -
2026-09-10": the shipped engine is rebuilt on the coherent wrong model it was claimed to
embody, the brief states behaviour rather than procedure, and a family charge is added whose
fast path is a derivation about the stamp tree rather than a running total per line.
