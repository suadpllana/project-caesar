We do reinforcement learning post-training with an in-process rollout engine, and the
engine has started handing back samples that do not belong to any policy we ever held.
The engine is in /app. A trainer pushes parameter updates into it between rollout
batches, some into the base weights and some into one adapter at a time, and it keeps
serving across those pushes, with a paged key/value cache and a prefix index in front of
it so that a group of samples sharing a prompt does not pay for that prompt more than
once.

You can see it with /app/run_rollout.py, which runs a short scenario: two requests on the
same prompt, three scheduler steps, a push into the first layer's key projection, then the
rest of the run. Request r0 comes back as 24, 10, 42, 35, 35, 54. On an engine started
fresh on the parameters that push left loaded, the same request gives 20, 52, 28, 3, 48,
37. On the parameters that were loaded before it, 24, 10, 42, 27, 15, 22. What we get is
neither of those: the first three tokens are the old policy and the rest are the new
policy attending to key and value projections that were computed under the old one. Every
sample in flight across a push looks like this, and an advantage computed from a sample
that cannot be attributed to one policy is worse than no sample at all.

I want the engine to give back, for every request that finishes, exactly the token stream
that request would have produced on an engine started fresh on a single parameter state,
while the cache carries on doing its job. Those two things together are the task, and the
second one is not a nicety: we sized this loop around the prompt sharing, and an engine
that stays correct by throwing the cache away after every push is not one we can run.

The rules I need it to follow.

If a push lands while a sample has already emitted tokens, and it moved that request's
effective parameters, throw those tokens away and generate the sample again from its
prompt. What comes back has to be identical to the same request submitted fresh against
the loaded parameters, sampler state included, so it counts from the start rather than
carrying on where it left off. Where a push discards more than one sample, they go back to
the front of the waiting queue in the order they were being scheduled in.

Nothing happens to a request when the push leaves its effective parameters where they
were. That covers the two cases we actually hit: the optimizer step that gets
rejected and replayed, so the values arriving are the values already loaded, and the push
that goes into one adapter while other requests are running under the base policy or
under a different adapter. Neither discards a sample, and neither costs a recomputation.

A cached block may only stop being used when what it holds could have changed. Requests
running under different adapters, and requests running under an adapter and under the base
policy, share their cached blocks whenever the contents of those blocks cannot differ
between them, and a push that cannot have moved what a block holds leaves that block in
service. I am asking for the whole of this, not the safe half of it: keeping a block that
should have gone and dropping a block that did not have to go are both wrong, and both
are measured.

The offload path has two levels and they are not the same. Level 1 copies the pages out
and back, so every cached block survives the cycle intact. Level 2 gives the pages up, and
what comes back is whatever the allocator had; nothing computed before that point may be
served afterwards. Neither level may change a single token of any sample.

Everything else about how the engine runs stays as it is: which requests are admitted in a
step, how many run at once, which request is preempted when the pool runs dry, and which
cached block is evicted first. I am not asking for a better scheduler, and a run whose
admissions, completions and preemptions come out in a different order is not the same
engine.

You may edit exactly these four files: /app/model/pstore.py, /app/runtime/pfx.py,
/app/runtime/sch.py and /app/mem/pool.py. Those four are the only paths that are taken
from your container, so nothing else you change or add is read, including new modules of
your own. The rest of the tree is restored from a clean copy before your work is measured,
and it has to keep working against that copy.

/app/run_rollout.py takes a scenario file as its argument and prints what the engine did
with it, so you can put the engine through whatever op sequences you want to convince
yourself. Everything is integer arithmetic and deterministic, so a run either matches or
it does not.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
