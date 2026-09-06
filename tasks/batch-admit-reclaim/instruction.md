The tree under `/app` is the scheduling end of our serving engine. Requests turn up with a prompt, the engine works through whatever is in the pool a step at a time, and every token a request produces is written down in the set file instead of being sampled, so a run here is a replay of traffic we have already served. `/app/traces` holds three of those sets. `/app/run_serve.py` takes one and prints what the engine did, a line to a line. The engine is under `/app/eng`. It is the only account of itself there is, and it covers how a block is identified, when one is handed back, what a step does and in what order, and what the `pool`, `block` and `batch` figures at the top of a set file govern.

Run it on `/app/traces/twin.txt`. `r0` and `r1` turn up together carrying the same six tokens, both come in on step 0, and the second line reads `r1 admit 0 from 0`. Six tokens of `r1` were in the pool already, put there by `r0` on that same step, and `r1` worked through all six of them again. That took most of the step. It is why `r2` waits until step 4 for room that was never short.

We rewrote the part that settles the scheduling and it has been wrong since. Four files hold it. Three of them are wrong.

A request comes in on the first step it could have come in on, and not before, which is to say the first step where the pool could hold everything it was holding once that step had run, without a request being put out on its account, and where the tokens it had to work through fitted in what was left of the allowance for that step. Both directions cost the same. Letting a request in on a step where the pool could not have held it is wrong, and holding one back on a step where it could have come in is wrong just as much, so a submission that turns cautious and waits for an empty pool every time fails as hard as one that admits everything and lets the engine sort it out.

When the pool runs out of room it gives up the block that has gone longest without being taken, the older of the two where two were last taken on the same step. A block in use is never given up.

A request that comes back starts working from the first token whose block the pool no longer has, and it starts from there whatever survived further along. One that has never been in the pool starts on the same terms. It takes whatever of the front of it somebody else has already put there.

Waiting requests are taken in the order they arrived and a request that has been put out keeps its arrival place. Out goes the latest to have arrived.

The sets we grade are not gentle. Requests do turn up carrying the same tokens as each other and do come in on the same step, and two of them do fill the same new block on one step. A request is put out and comes back more than once. The block the pool gives up is sometimes one in the middle of what a request holds, not one at either end. A request finishes on the step another is put out, and one is put out on the step it would have finished. There are prompts that end exactly on a block edge and prompts shorter than a single block. There are requests too large to come in under the allowance at all, which wait for an empty pool.

Every line the engine prints names a request and then one of `admit`, `preempt`, `resume` and `done`, with the step it happened on. An `admit` and a `resume` carry `from` and the token the request starts working from, and a `preempt` carries `at` and the count of tokens the request had produced by then. The order the lines come out in is the order the engine did the things, and it is not yours to change.

You may edit `/app/eng/fit.py`, `/app/eng/room.py`, `/app/eng/back.py` and `/app/eng/pick.py`. Nothing else. Every other file is compared against the shipped copy once your work has run, not all four of those need changing, and the interfaces are frozen, so keep each function that is there with the arguments it has.

We grade the lines in order, exactly, with no partial credit, and we grade the three sets in `/app/traces`, a harder set you have not seen, and several hundred more built after you have finished. A rule fitted to those three will not carry. The verifier allows 600 seconds for the complete run. No expected output sits anywhere in your tree. None is coming.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
