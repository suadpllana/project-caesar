`/app` is the container our services are wired through. Registrations name a
lifetime, scopes open and close around a unit of work, and when a scope closes
the container tears down whatever belongs to it. We rewrote the ownership and
teardown decisions last cycle and it has been wrong since.

Run `/app/run_wire.py` on `/app/cases/wide.txt`. The third line back reads
`torn pool 1 app`, and that line should not exist: `pool` was pulled in
underneath `app`, which is a singleton and outlives every scope in that
stream, so when scope 1 closed the container reached inside a live
singleton and disposed of a dependency it is still holding, while `app`
itself has not been torn down at all and will not be. There are six more
case files in `/app/cases`. None of them comes out right either.

`/app/wire/own.py`, `/app/wire/pin.py`, `/app/wire/hold.py`, `/app/wire/gate.py`,
`/app/wire/tear.py`, `/app/wire/shut.py` and `/app/wire/plan.py` are yours to change. Some of them
are right. `/app/wire/core.py`, `/app/wire/reg.py` and `/app/wire/scope.py`
are the container itself and you may not touch them. Read them anyway. They
already settle things the editable files have to agree with.

We grade the dump, line for line, in the order it comes out. A teardown is
`torn`, then the registration name, then the scope that owned the instance,
then the name we were asked for when it came into being, which for anything
pulled in underneath something else is the name at the top of that
resolution and not the dependency's immediate parent; a declined
resolution is `refused`, then the name, then the scope we were in. Those two
words are the only record kinds we write and we match them exactly.

Some ground rules, because several of them are not what you would do
elsewhere.

An instance is owned by the scope its holder was built in, and that scope is
the one that tears it down. A singleton is built once, is owned by the root,
and everything it pulls in is owned by the root along with it, however deep
the chain runs and whatever lifetime those dependencies declare for
themselves, so a transient two steps below a singleton belongs to the root
exactly as the singleton does and survives every scope that opens and closes
around it. A scoped registration resolved twice inside one scope is one
instance, not two. Within a scope, teardown runs back to front against the
order the instances were created in. Back to front, every time. Closing a
scope tears down nothing an ancestor owns, and an ancestor's instances stay
live exactly as long as the ancestor does.

A registration can carry a mark, and one that does is owned by the nearest
scope in reach carrying the same mark, and not by the scope the work was
charged to. The nearer mark wins. A
registration can also wrap another, in which case the wrapped one is built
first and torn down after its wrapper. Outside in. And a registration can declare a
parting call, a name we resolve as the instance is torn down, charged to the
scope outside the one that is closing, because that scope is on its way out
and nothing may be built into it any more.

We refuse to resolve a singleton that can reach a scoped registration
anywhere below it, through its own dependencies or through theirs, however
many steps down the chain that takes, and a refusal builds nothing at all,
so no part of the chain underneath it is created and nothing from that
attempt is ever torn down. We refuse a marked
registration when no scope in reach carries its mark, we refuse anything
whose dependencies or wrapping come round in a circle, we refuse a parting
call that cannot be resolved where it has to land, a close with no scope
open, and invoking a factory whose holder has not been resolved yet. Each of
those is a `refused` line and nothing else.

A scope that closes owning nothing prints nothing at all. A refusal is written
at the point we declined it and never held back to the end, so the dump for a
stream that mixes the two reads in the order the two kinds actually happened.

A component can hold a factory for another registration, and it can invoke
that factory inside a scope that was opened after the holder itself was
built. The streams we grade do that. They do it more than once against the
same holder, sometimes with a further scope opened in between and closed
again before the next invocation, and a holder whose own lifetime is
transient behaves no differently from any other holder when they do it.

Two things we do not read.

Nothing turns on the order two separate scopes are torn down in relative to
each other, because what we compare is the order inside each scope; instance
numbers are yours entirely.

The dump has to describe the run that produced it.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
