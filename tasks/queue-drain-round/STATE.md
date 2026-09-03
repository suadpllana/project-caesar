# queue-drain-round

Scratch for the next session. This never ships; `scripts/package.py` drops it.

## What it is

A clearing house over a handful of members. Obligations queue at the payer in the order the
house wrote them down, each with a day it falls due, and a round settles at every tick. The
graded artifact is the record the book keeps plus the sheet of what became of every
obligation. No work counter anywhere in it.

## The strategy

- Why a frontier agent cannot one-shot the plan: the natural plan is a pipeline - work out what each member can afford, move that, give up on
whatever is left - and it is wrong twice over. It cannot clear a ring, because a member with
nothing in hand can still pay when the money reaches it inside the same round; and once that
is understood, the natural repair is to net the fronts of the queues and go round again,
which is still wrong whenever a member has to pay more than one of its obligations before its
own money comes back. The answer is the largest choice of how far down each line the round
gets, taken jointly. Nothing in the tree confirms any of it: the book applies whatever it is
handed and records what happened, so every wrong reading produces a book that balances.

- Tactics making that true: A1, A2, B1, B2, C1, C2, C4 - prong A because the pipeline reading is the memorised one and is specifically wrong, prong B because the requirement is stated and what it implies lives only in the book's behaviour, prong C because nothing fails until the verifier and three hundred streams are built after the submission is sealed.

## The self-attack

- My own attack on the plan: my first plan was to pay each member's queue from its balance until it stalls and cancel the
rest at the cut-off, which is exactly the shipped tree and which loses a fifth of the graded
streams outright. My second plan was to net the heads of the queues and iterate, which is
wrong on a quarter of them. I could not have committed to the depth formulation without
sitting down with the requirement and asking what "leaves nothing on the table" means when
payments are simultaneous.

## The band

- Estimated solves out of 8: 2, designed at 1 and allowing for the usual drift upward.

## Contract, frozen before the environment was written

Graded, exactly: the record the book keeps, split into rounds at each close - inside a round the
obligations moved are a set and the ones given up on are a sequence, because oldest-first is a
stated rule and nothing decides how many times a submission calls the book - plus every member's
holding at each close, plus the sheet (per obligation: paid, gone or open, and the tick). Both
are produced in `house/bk.py`, which is not editable. `tests/oracle.py:rounds` is the single copy
of that canonicalisation. Not graded: how many times a round asks for a plan, how many turns its
loop takes, how it partitions its calls to the book, what it caches, which data structures it
holds.

Artifacts: `/app/house/drn.py`, `/app/house/gvp.py`, `/app/house/rnd.py`, `/app/house/due.py`.
`due.py` needs no change and that is deliberate.

## Numbers measured on this build

- Shipped tree: correct on 13 of 33 enumerated streams.
- Wrong readings, share of generated streams they get wrong: pay-what-you-hold 83%,
  net-the-heads 23%, give-up-in-bulk 90%, blocker-does-not-block 96%, day-does-not-matter
  100%, one-pass-round 100%, give-up-newest 100%, never-short-of-anything 100%.
- Reference against the sealed model: 0 disagreements on 400 generated streams; both agree
  with an exhaustive search over depth vectors on 600 small rounds, which also proves the
  largest standing-up answer is unique.
- Seven alternative correct implementations agree on 153 streams, among them one that hands the
  book its round in several motions and walks the members backwards. Graded as a raw row
  sequence that one disagreed on 136 of 153, which is the run-audit exposure the per-round
  comparison closes.
- Renaming every member and obligation moves nothing on 233 streams.
- Two-image trial: oracle 1, nop 0, 29 cheats 0.

## Gates not run

The three-agent probe has NOT been validly run, and the owner has asked that probe subagents
not be spawned at all - they burn the whole five-hour account limit in minutes. One agent did
finish a contaminated run (the harness injects CLAUDE.md, which names this task's wrong
readings and their hit rates) and solved it; that number means nothing. What the run was worth
was its account of the brief, and the three leaks it named are fixed: the simultaneity
statement is out of the brief and back in `bk.Book.move` where it is discoverable, the worked
example is no longer annotated, and the input-space sentence no longer carries its "because"
clause. Expect the pipeline's easiness probe to be the first real measurement.

Also not run: `harbor check` (harbor is not installed here).
