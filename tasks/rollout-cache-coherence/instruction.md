We do reinforcement learning post-training against a rollout engine that stays up across
weight pushes, and it has started giving back samples that belong to no policy we ever
held. The engine is in /app. A trainer pushes parameter updates into it between rollout
batches, some into the base weights and some into a single adapter, and it keeps serving
through those pushes, with a paged key/value cache and a prefix index in front of it,
because a rollout group is many samples on one prompt and we do not pay for that prompt
more than once. Your job is to make every request that finishes come back with the token
stream it would have produced on an engine started fresh on one parameter state, and to
do that without giving up the reuse.

/app/run_rollout.py runs a short scenario that shows it: two requests on one prompt, three
scheduler steps, a push into the first layer's key projection, then the rest of the run.
Request r0 comes back as 24, 10, 42, 35, 35, 54. Start an engine fresh on the parameters
that push left loaded and the same request gives 20, 52, 28, 3, 48, 37. On the parameters
loaded before it, 24, 10, 42, 27, 15, 22. Ours is neither. The first three tokens are the
old policy and the rest are the new policy attending to key and value projections computed
under the old one. Anything in flight when a push lands comes out like this, and a sample
we cannot attribute to one policy is a sample we cannot compute an advantage from.

Some ground rules, because a few of them are not what you would do elsewhere.

A sample that has already put out tokens is done for when a push moves the parameters its
request runs under. Throw those tokens away and generate it again from the prompt. What
comes back has to be what the same request gives submitted fresh against the loaded
parameters, sampler state and all, so the counting starts over rather than carrying on
from where it stopped. Where one push takes down several samples, they go back to the
front of the waiting queue in the order they were being scheduled.

A push that leaves a request's effective parameters where they were does nothing to that
request. Two of those come up constantly here. The optimizer step that gets rejected and
replayed pushes the values that are already loaded. The push into one adapter arrives
while other requests are running on the base policy or on a different adapter. No sample
goes down for either of them, and neither costs a recomputation.

A cached block stops being used only when what it holds could have come out different.
Requests on different adapters, and requests on an adapter and on the base policy, share
blocks wherever the contents cannot differ between them. A push that could not have moved
what a block holds leaves that block in service. Both halves of that are measured: a block
kept that should have gone is wrong, and so is a block dropped that did not have to go.

The offload path has two levels and they do not do the same thing. Level 1 copies the
pages out and puts them back, so a cached block comes through the cycle intact. Level 2
gives the pages up and what comes back is whatever the allocator had in them, so nothing
computed before that point may be served after it. No token moves at either level.

Leave the rest of how the engine runs alone. What gets admitted in a step, how many run at
once, what gets preempted when the pool runs dry, what gets evicted first: none of that is
what we are after, and a run whose admissions, completions and preemptions come out in a
different order is a different engine.

Four files are yours: /app/model/pstore.py, /app/runtime/pfx.py, /app/runtime/sch.py and
/app/mem/pool.py. Those four paths are the only ones we take out of your container, so
anything else you edit or add, new modules of your own included, is not read. The rest of
the tree goes back to a clean copy before your work is measured and has to keep working
against that copy.

/app/run_rollout.py takes a scenario file as its argument and prints what the engine did
with it, so put it through whatever op sequences you want. The arithmetic is integer
throughout and the engine is deterministic, so two runs of one scenario agree exactly.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
