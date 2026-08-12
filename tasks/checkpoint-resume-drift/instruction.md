Our post-training jobs get preempted, so they checkpoint and come back, and the run that
comes back is not the run that went down. Nothing raises. The loss curve keeps its shape.
We caught it because a rerun from one checkpoint landed somewhere else, and then because
two relaunches off that same checkpoint disagreed with each other by the third optimiser
step. The trainer is in /app.

/app/run_train.py drives the short version with /app/conf/demo.json: five microbatch
fills, a checkpoint, two more fills, the process thrown away, a load, four more fills. It
comes back announcing step 0 in its trace when it went down at step 2, and it finishes on
parameters 599807, 726141, 773678. Take the save out of that scenario. Take out the kill,
take out the load, take out the two fills the load rolled back, then run what is left
through the same trainer. It finishes on 355362, 554625, 575283, at step 4. That second
run is what we should be getting. The first one is training something else.

Some ground rules, because a few of them are not what you would do elsewhere.

A load throws work away, and that is fine. Everything between the checkpoint a load
restores from and the load itself is gone: those fills ran, they cost the sample store
real reads and cost the model real positions, and not one of them reaches the parameters
the run ends on. The rest of it is what has to hold. From the load onward the trainer must
be on the path it would have been on had it never been interrupted at all, parameter for
parameter, with the same shadow average, at the same step, with the same record of every
microbatch and every update it has written since.

The settings live with whoever relaunches the job. They are not in the checkpoint and they
must not come out of it. We change them between a kill and a load constantly, a shorter
warmup or a different sequence-length curriculum or a longer accumulation window, and the
job that comes back is expected to honour what it was relaunched with; so everything the
amended settings reach has to follow the amendment from the load onward, and everything
that was already fixed before the save has to come through the load untouched, which
cuts both ways and is measured both ways. A value that goes on being derived after the
load is wrong if it was pinned before the save. A value that was pinned before the save is
wrong if it gets derived again afterwards.

The channel the checkpoint goes through is small. It carries a vector of integers, it
refuses a payload longer than it holds, and the sample order on its own is larger than the
whole payload, so writing out everything that offers you a snapshot is not a plan that
survives contact with it. Which parts of the trainer are worth the slots is the question.
Answer it. Do not work around it.

A resume must not cost the stream anything the run it continues had not already paid. We
count what the sample store hands out, what goes through the model, how many updates the
optimiser applies, all of it in files you cannot edit, and we compare those totals against
what the work actually was. Rebuild your position by replaying the stream from the top of
the epoch and you get the parameters right while reading the store hundreds of times more
than the run you are continuing ever read it. That fails.

Nothing about the shape of the payload is measured. Slot order, framing, which holders you
name, how you encode an empty slot: your call entirely, as long as the channel takes it.
How many times you ask the sampler for a sample is not measured either.

Leave the rest of the trainer alone. How the packer fills a bin, how wide a bin is, what
the schedule computes, which sample comes next: none of that is what we are after, and a
run whose microbatches and updates come out in a different order from the one you were
handed is a different trainer.

Four files are yours. They are /app/train/ckpt.py, /app/data/feed.py, /app/train/noise.py
and /app/train/sched.py, and those four paths are the only ones we take out of your
container, which means anything else you touch is not read, and that covers new modules of
your own, helper scripts, edits to the files around them, whatever you leave lying about
in /app; the rest of the tree goes back to a clean copy of what you started with before
any of this is measured, and your four have to keep working against that copy, not against
a tree you reshaped around them.

/app/run_train.py takes a scenario file as its argument and prints what the trainer did
with it, so put it through whatever sequence of fills, saves, kills, loads or amendments
you like. /app/conf/demo.json is the format. The arithmetic is integer the whole way and
the trainer is deterministic. Two runs of one scenario agree exactly. Anything that moved
between them moved because you moved it.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
