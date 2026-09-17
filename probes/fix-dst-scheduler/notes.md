# fix-dst-scheduler, round 1: easiness probe 2 of 3

Three trajectories, `round1-trial{1,2,3}.md`, the agents' own words with the pasted brief
removed. The files carry no verdict; which one failed is not recorded. The best guess is
trial 3: its closing summary lists every repair the other two list except waking the loop
when a pool day rolls over, and `no-cap-wake` is a reading the population separates on 8.3
per cent of plans. That is a guess and is marked as one.

What all three did, in the same order:

1. One command: `cat` every file in the tree and both plans.
2. One thinking step: a list of every defect, found by reading the shipped code against the
   brief sentence by sentence - the fold taken early, the gap fallback, clock advanced in
   elapsed time, follow chained off the nominal, the closed-form deadline, the ledger keyed
   to the job's zone, the charge at the end, no wake at a pool day.
3. One heredoc rewriting all four files. Trials 2 and 3 were correct on both shipped plans
   at that point. Trial 1 hung on a follow-chain bookkeeping slip, traced it in six commands,
   fixed it.
4. A brute-force check of the zone helpers and a timing run, then done. Trial 3 also
   hand-checked three lines of the shipped plans.

Where the plan came from: not the brief's prose in the sense leakcheck measures - the one
shared phrase is the gap-resolution convention, which the contract requires and which every
agent quoted back in its summary. It came from the shipped `lane.py`: the loop already had
the right phases in the right order (`finish`, `arrive`, `expire`, `launch`), priority
arbitration, the skip rule and deadlines as candidates, and `due.nom_at(job, k, prev)`
already carried a `prev` slot. Every defect sat in one small function whose behaviour is
one sentence of the brief. "Fix each function to match its sentence, and replace the
up-front expansion with lazy generation" was a plan the agents formed before writing a
line, and it was the correct one.
