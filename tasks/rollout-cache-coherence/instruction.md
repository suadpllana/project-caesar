We run reinforcement learning post-training against a rollout engine that stays up across
weight pushes, and it is handing us samples that belong to no policy we ever held. The
engine is in /app. A trainer pushes parameter updates into it between rollout batches,
some of them into the base weights and some into a single adapter, and the engine keeps
serving straight through those pushes, with a paged key/value cache and a prefix index in
front of it, because a rollout group is many samples on one prompt and there is no reason
to pay for that prompt more than once. Your job is to make every request that finishes
come back with the tokens it would have produced on an engine started fresh on one
parameter state, and to do that without giving up the reuse.

/app/run_rollout.py runs the short version of it: two requests on one prompt, three
scheduler steps, a push into the first layer's key projection, then the rest of the run.
Request r0 comes back 24, 10, 26, 45, 63, 34. Start an engine fresh on the parameters that
push left loaded and r0 gives 20, 52, 28, 3, 48, 37. Run it on the parameters that were
loaded before the push and you get 24, 10, 42, 27, 15, 22. Ours is neither. The first two
tokens are the old policy, the rest are the new policy attending to key and value
projections that were computed under the old one, and everything in flight when a push
lands comes out of the engine like that. We get a few in every batch. A sample that
belongs to two policies is no use to us.

Some ground rules, because several of them are not what you would do elsewhere.

A sample that has already put out tokens is finished the moment a push moves the
parameters its request runs under. Throw those tokens away. Generate it again from the
prompt, and what comes back has to be what that same request gives when it is submitted
fresh against the parameters now loaded, sampler state and all, counting from zero instead of
carrying on from wherever it had got to, because a resumed counter gives a different
stream and we are back where we started. Where one push takes down several samples at
once, they go back to the front of the waiting queue, ahead of anything that has not
started yet, in the order they were being scheduled in.

Tokens are not all a request is carrying when a push arrives. Whatever key and value work
it has already done for itself sits in the same position as anything else the engine has
cached: it stands where the push could not have moved it, and where the push could have
moved it, the request has to do it over. Both directions cost us. A request that has not
put out a token has nothing to throw away, so it is none of the samples we count as thrown
away and it keeps the place in the queue it already had; what it has computed is the whole
of what is at stake for it.

A push that leaves a request's effective parameters exactly where they were does nothing
to that request at all. Two of those come up here constantly. An optimizer step that gets
rejected and replayed pushes the values that are already loaded. A push into one adapter
lands while other requests are running on the base policy, or on some other adapter.
None of them care. No sample goes down for either case, and neither one costs a
recomputation.

A cached block stops being used only when what it holds could have come out different.
Requests on different adapters share blocks, and so do a request on an adapter and a
request on the base policy, wherever the contents of those blocks cannot differ between
them; a push that could not have moved what a block holds leaves that block in service.
Both halves are measured. A block kept that should have gone is wrong. A block dropped
that did not have to go is wrong too.

The offload path has two levels. They do not do the same thing. Level 1 copies the pages
out and puts them back, so a cached block comes through the cycle intact and is still
worth a hit on the other side. Level 2 gives the pages up, and what comes back is
whatever the allocator had in them, so nothing computed before that point may be served
after it. No token moves at either level.

Leave the rest of the engine's behaviour where it is. What gets admitted in a step, how
many run at once, which request is preempted when the pool runs dry, which cached block
goes first when something has to be evicted: none of that is what we are after, and a run
whose admissions and completions and preemptions come out in a different order from the
engine you were handed is a different engine.

Four files are yours. They are /app/model/pstore.py, /app/runtime/pfx.py,
/app/runtime/sch.py and /app/mem/pool.py, and those four paths are the only ones we take
out of your container, which means that anything else you touch is not read, and that
covers new modules of your own, helper scripts, edits to the files around them, whatever
you leave lying about in /app; the rest of the tree goes back to a clean copy of what you
started with before any of this is measured, and your four have to keep working against
that copy, not against a tree you reshaped around them.

/app/run_rollout.py takes a scenario file as its argument and prints what the engine did
with it, so put it through whatever sequences of adds, steps, pushes, sleeps, wakes you
like. The arithmetic is integer the whole way and the engine is deterministic. Two runs of
one scenario agree exactly.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
