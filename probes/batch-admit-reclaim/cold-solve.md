My own words, written while solving the task from the shipped tree and the brief
alone. No file under tests/ or solution/ was open while any of this was written.

## The plan, before I opened a file

Build a refcounted table of blocks keyed by the whole prefix through the end of
each one. Keep the unreferenced ones in a queue ordered by last use. For the
entry question, count the blocks the newcomer is missing, add one for its part
block, and compare that with the slots the pool has free plus the ones it could
give up. Check the allowance the same way, target length minus wherever the
request starts. For the block to give up, take the least recently used. For where
a request starts, walk its blocks from the front and stop at the first one the
pool no longer has. Leave the arrival order and the choice of victim alone.

I wrote down at the time that I expected to be wrong nowhere on this plan.

## What happened

The count is wrong and it is wrong in a way running the thing does not show. Two
separate reasons, and I found the first only because I went back and read the
step driver line by line rather than skimming it.

The first is that the entry question is settled before the step decodes and
applied after it. So the count has to be a count of the pool the step is going to
leave behind, not the pool in front of me. Decoding is not neutral: a part block
that fills is looked up and, when the pool already holds that content, the request
hands its own block back, so the step gives blocks up as well as taking them.
I patched the count for that.

The second I got wrong twice. A request that finishes on the step releases its
blocks, and I counted those releases as room. They are not room. Nothing is
removed from the pool at the moment a block stops being used; it stays with its
contents until something needs the slot. I had actually read the line in the pool
that does this - it drops a reference and nothing else - and I still wrote the
count the other way, because a release looks like a free.

The patched count still failed. What worked was stopping counting: copy the pool,
play the rest of the step out on the copy in the order the driver does it, and see
whether the entry succeeds. That is when it passed.

## Where I got confirmation, and what I had to guess

Confirmation: nowhere. The engine prints a timeline under every version I wrote
and all of them look reasonable. The tokens each request produces come out of the
set file, so they are identical whether the policy is right or wrong, and there is
nothing to diff. I could not tell a good version from a bad one by running it. I
knew the count version was wrong only because I later reasoned it through, not
because anything failed.

Two things I had to guess:

  Whether the entry test should fail when the step would have put somebody out
  anyway, or only when the newcomer is the reason. I took the second reading.

  Whether "everything it is holding" includes the part block at the end. I took
  yes.

Both guesses turned out right, but they were guesses.
