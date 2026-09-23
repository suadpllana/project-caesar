What the easiness probe of 23 September 2026 measured, and what was done about it.

Three trials against the bundle at commit f31b80c. All three solved it. The contributor supplied
the three transcripts as one zip; they are beside this file with the brief stripped from the top
of each (lines 1-13 or 1-14, up to and including the time-budget sentence), so that
`tools/leakcheck.py` compares the solver's words against the brief rather than the brief against
itself. Nothing else was changed.

`python tools/leakcheck.py partial-key-purge <the three files>`: nothing above the floor in any of
them. The plan did not come from quoted prose.

What all three have in common is the moment the plan was fixed. Each read `run_db.py`, the nine
modules and the four sample scripts in one or two tool calls, and wrote its complete plan before
running a single experiment:

  trial 1   "rewrite the five permitted modules with an indexed fixpoint delete and a tree-DP
            audit" - the audit folds the cascade structure into a forest, strongly connected
            components for loops and self-matching rows, every per-row effect "a few path
            updates summed over subtrees", and a per-row fallback for any component the forest
            cannot express
  trial 2   "a cell-based index ... batch-process the single-parent forest bottom-up with a
            fallback for cleared-but-referenced tables" - counters per match cell, small-to-large
            merging of child states, cycles judged together, per-row judging as the fallback
  trial 3   profiled deep.txt first (cycles, depth, branching), then "an exact engine for delete
            and an incremental closure-merging pass for audit" - "single-row closures form a
            laminar family", Tarjan components, and the exact engine for seeds whose
            contributions cannot be aggregated

The delete was a counter fixpoint in all three, from the first draft. The audit's structure -
the removed sets of lone deletes nest, so they are the subtrees of one tree - was each agent's
first idea, named in its own words ("forest", "laminar family", "the parent's delete contains
the child's"). None of them met the sentence the design put the second discovery behind.

How each checked itself: a brute-force transcription of the brief (all three), random script
generators modelled on the shipped schema and then on random schemas (1,000 to 2,000 scripts
each), a comparison of the fast audit with its own exact engine on sampled rows of deep.txt
(trials 1 and 2) and on all 36,067 rows (trial 3), and subsampled deep stores small enough for
the brute force (trial 2). Trial 3's fuzzing found one real bug in its fast path (a row that can
never force itself out inheriting failures recorded about itself from merged sub-closures) and
fixed it. Every rule of the brief was confirmed on its own against the brute force.

Timings they reported: deep.txt in 4.2 s, 3.4 s and 7.2 s; estimates for the graded set of 42 s
and 55 s against 180 s. Each fallback to per-row replay stayed cheap because the deep stores hold
few rows the tree cannot express (246 multi-match revisions and 109 small loop components in
deep.txt), and the deep schema is fixed, so trial 2's whole-audit fallback (a clearable table
that is referenced) never fired.

The repair is recorded in tasks/partial-key-purge/STATE.md under "Easiness recovery -
2026-09-23 (probe 3 of 3)".
