What the easiness probe of 2 September 2026 measured, and what was done about it.

The probe returned **3 of 3**. Three trajectories were supplied and all three read the same
way: read the six source files, then **one write of the finished policy**, before running a
single experiment. No intermediate wrong version in any of them. Then each built its own
fuzzer, asserted its own reading of the invariant, watched it go green, and stopped.

The plan came from the brief. Two sentences did it, and `tools/leakcheck.py` names both:

    A task is worth its own priority, or the highest priority among the tasks that are
    waiting, however far back, for something it is holding, whichever of those two is
    greater. Nothing else.

    Everything the decision needs is reachable from the core object you are handed: who holds
    what, who is queued on what, what each task started as, and what it is worth at this
    moment.

The first is the closed form of the answer. STATE.md lists three findings the task is built
on - release is a recompute rather than a restore, blocking is not one deep, and a timeout
lowers a boost - and that one sentence hands over the first two outright and makes the third
fall out for free. "however far back" is the transitive chain. "whichever of those two is
greater" is the max. "Nothing else" is the over-lift fence. All three agents wrote it back in
the brief's own vocabulary: "directly or through a chain of holders", "directly or through a
chain of other blocked tasks", "through a chain of held mutexes".

The second sentence says the answer is a pure function of live state and then enumerates that
state, which is why nobody reasoned about the four hooks at all. All three made every hook
call one recompute.

Two more sentences were removed for the same reason, neither of them found by leakcheck. The
handover paragraph explained *why* the acquire hook exists ("It is also why the moment a mutex
changes hands is one of the four moments you are given at all"), which is the discovery that
a FIFO handover leaves the new holder with a queue. And the timeout paragraph ended "the queue
behind it is one shorter than it was a tick ago", which points at the holder - and STATE.md
calls the timeout "the one measured solutions miss".

What replaced them is the requirement rather than the reasoning: nothing may sit waiting
behind a task it outranks, and nothing may be worth more than the priority it started with
unless a task waiting on it accounts for the difference. Both directions, stated plainly, and
the closed form is derivable from them without being written down. Plus one input-space
sentence, which is the `guard-mark-unwind` move: a task that is waiting can be holding
something of its own, with a queue of its own behind it, and the graded set does that. That
says the shape occurs and is graded; it does not say what follows from it.

Measured. `leakcheck.py` against these three trajectories: two findings before, none after.
That is the only evidence available for a mode-A repair, because all three submissions are
**correct** - each was reconstructed from its own trajectory and graded through the real
verifier at reward 1, drawn scenarios included. No change to the verifier can fail them and
none should. One of them ships as `authoring/variants/ok-probe-solve` and must keep scoring 1.

Worth knowing before reading this as evidence about difficulty: all three submissions are the
same shape as `authoring/variants/ok-full-solve`, which was written before the probe ran. The
route was foreseen. What was not foreseen is that the value the route computes was printed in
the brief, so nobody had to derive it.

Not re-probed. The three-agent local probe is the next thing to run on this task.
