A merge job in `/app` is losing data.

The store keeps records in immutable segments. Writers append. A flush seals whatever has
accumulated into a new segment at the front, and a merge job folds the newest few segments
into a single one, dropping whatever it decides no reader can still reach. Readers hold read
points, and a read taken at a read point has to answer exactly what it would have answered had
no job ever run. That is the part that has stopped being true.

Drive the shipped engine over a short stream and watch it go. Set key 4 to 120 and key 7 to
15, flush. Adjust key 4 by -30, delete key 7, flush. Adjust key 4 by 8, set key 9 to 3, flush.
Merge. Before the job the store answers 98 for key 4. Afterwards it answers 8. Key 7 and key 9
come through untouched, so from the outside there is nothing to see, and the counters are no
help either: the job pulled 6 records out of the three segments it took, wrote 3 into the one
it produced, and asked the rest of the store nothing at all.

Rewrite `/app/merge/plan.py` so that a job preserves every read and costs what it has to cost.
Both halves are graded. Neither is optional.

The reads come first. After every job, and once more when the stream is over, the store is
asked for every key it has ever held at every read point it is currently holding, and each of
those answers has to match what the same stream produces with no merging anywhere in it; a
read point taken twenty operations ago binds a job exactly as hard as the one at the head of
the stream binds it, and a job that satisfies the head and quietly moves an older one has
failed. What an answer is, and which records take part in producing one, is in
`/app/seg/read.py`, with the record kinds in `/app/seg/rec.py`. A job may change how many
records it takes to produce an answer. It may not change the answer.

Then the work, on three counters kept in `/app/merge/core.py`, outside the file you are
editing. A read is one record pulled out of the job through the cursor you are handed. A write
is one record placed into the output segment. A probe is one point read against the segments
this job does not own. All three are graded against a budget, and each budget is what the
cheapest correct merge this store allows actually spends on that scenario. We do not publish
where any of them sits. So a plan that answers every read and spends more than it needed to
fails, in the same way and for the same reward, as one that answers a read wrong; a plan that
comes in under a budget is welcome to. Nothing else about the output segment is graded: how
many records it carries is yours, so are their order and their sequences, and two plans that
answer every read the same way are both right however far apart their output segments look.

There is a rule about where an output record may come from, and it is checked. Every record a
job writes has to be one that the records it pulled for that key determine, and it has to sit
at the sequence of a record it pulled. Reaching a segment behind the cursor, or recognising a
stream and writing the answer out of memory, produces records the job cannot account for, and
that is a failure on its own even when every read comes out right. Probes are held to the
same standard: what one reports has to be what the rest of the store holds.

Some ground rules, because a couple of them are not what you would do elsewhere.

The schedule is not yours. Which segments a job takes, the order its keys are visited in,
where the read points sit, and whether a job runs at all are settled in `/app/merge/pick.py`
and `/app/merge/drv.py`, and the whole of it is compared against a recorded trace. A stream
that calls for a merge when there is nothing worth merging does nothing. That is correct
behaviour and not a case to fix.

The cursor gives you one key at a time, and gives that key's records newest first. Stop taking
them whenever you want. Whatever you did not take goes out of the store with everything else
you chose not to write, so the decision to stop is a decision about what survives, and the
records under the point where you stopped are gone whether or not you looked at them.

Two things are outside the job and stay that way. A key the job holds no record for is not its
business. Neither is a read point sitting below every record the job does hold for a key,
because the segments underneath are still answering that one and will keep answering it: they
are not rewritten, they are not consulted unless you consult them, and they are still there
under whatever the job produces.

Only `/app/merge/plan.py` survives. Every other file is restored from a pristine copy before
the scenarios run, so an edit anywhere else is discarded and never graded, and the counters and
the driver we measure you with are the ones that shipped. Keep the class name, the constructor
and the method the driver calls exactly as they are.

`/app/run_merge.py` takes a scenario file of operations and prints what the store answers, what
the schedule did, and what the three counters reached. Build as many streams as you want and
run them. The graded set is a different one. It is larger than the stream above, and it is
pointed at cases that one never reaches.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
