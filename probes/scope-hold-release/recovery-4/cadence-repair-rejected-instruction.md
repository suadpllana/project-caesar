`/app` is the container everything here is wired through. A registration names
a lifetime, scopes open and close around a unit of work, and when a scope
closes the container disposes of whatever belongs to it. We rewrote the
ownership and teardown decisions last cycle and it has been wrong ever since.
Run `/app/run_wire.py` on `/app/cases/wide.txt` and read the third line back.
It says `torn pool 1 app`, and that line should not be there at all: `pool`
came in underneath `app`, `app` is a singleton that outlives every scope in
that stream, and so closing scope 1 has reached inside something still live and
disposed of a dependency it is holding, while `app` itself has not been torn
down and never will be. There are nine more case files in `/app/cases`. None of
them comes out right either.

`/app/wire/own.py`, `/app/wire/pin.py`, `/app/wire/hold.py`,
`/app/wire/gate.py`, `/app/wire/tear.py`, `/app/wire/shut.py` and
`/app/wire/plan.py` are yours to change, and some of them are already right.
`/app/wire/core.py`, `/app/wire/reg.py` and `/app/wire/scope.py` are the
container itself and you may not touch them. Read them anyway. They already
settle things the editable files have to agree with.

We grade the dump line for line, in the order it comes out. A teardown is the
word `torn`, then the registration name, then the scope that owned the
instance, then the name we were asked for when it came into being, which for
anything pulled in underneath something else is the name at the top of that
resolution and not the immediate parent it hung off; a declined resolution is
`refused`, then the name, then the scope we were in when we declined it, and we
write that line where it happened and never hold it back to the end, so a
stream mixing the two reads in the order the two kinds actually occurred. Those
two words are the only record kinds we write. We match them exactly.

Some ground rules, because several of them are not what you would do elsewhere.

An instance belongs to the scope the work was charged to unless one of the
rules below moves it. A singleton is built once and is owned by the root, and
everything it pulls in belongs to the root too, however deep the chain runs and
whatever lifetime or mark those dependencies declare for themselves; that rule
wins over the mark. Finding an instance already built changes neither its owner
nor its cause. A scoped registration is reused by registration and build scope
together. A mark may send a teardown somewhere else. It does not move the
cache. Within a scope, teardown runs back to front against allocation order,
and the core sets aside an instance number before it goes on to build
dependencies or a wrapped registration, so those later allocations are disposed
of first. Back to front, every time. Closing a scope tears down nothing an
ancestor owns. A scope closing with nothing of its own prints nothing. The root
never closes.

A registration can carry a mark. Outside a singleton's chain, one that does is
owned by the nearest scope in reach carrying the same mark, starting from the
scope the work was charged to and walking out through its ancestors, and the
nearer mark wins; with no matching scope in reach its owner is the root. The
mark moves that instance and nothing else. Its dependencies keep their own
ownership rules, and neither its build scope nor its cache key travels with it.
A registration can also wrap another, and then the wrapper takes its number
first while the wrapped registration is allocated underneath it and disposed of
first; and a registration can declare a parting call, a name we resolve as the
instance is being torn down, charged to the scope outside the one that is
closing, because nothing may be built into a closing scope any more. That call
runs straight after the instance's own `torn` line.

Admission belongs to the name we were asked for. We refuse a requested
singleton that can reach a scoped registration anywhere below it, through
dependencies or through wrapping, however many steps down the chain that takes,
and we refuse a requested marked registration when no scope in reach carries
its mark. Both checks stop at the request. They are not started again for every
name pulled in underneath. Cycle detection does keep going, so a dependency or
wrapping cycle anywhere below the requested name refuses the whole request.
Failing admission builds nothing at all. We also refuse a parting call that
cannot be resolved where it has to land, a close with no scope open, and an
invoke of a factory whose holder has not been resolved yet. Each of those is
one `refused` line and nothing else. A refused invoke names the scope where it
was attempted and a refused parting call names the scope where it had to land.
Every name in the streams is registered. A factory declaration is not a
dependency.

Construction can fail after admission has let it through. The optional last
field on a registration line, the one after its parting-call name, is `fail`;
leaving it out or writing `.` means that constructor starts available. `o fault
NAME on` makes it unavailable and `o fault NAME off` puts it back. Those
operations print nothing. They do not change a registration and they do not
dispose of an instance already built. A cached instance is still usable while
its own constructor is unavailable. Otherwise the wrapped registration is built
first, then the dependencies in their listed order, and only then does this
constructor run, and if it is unavailable at that moment it fails, its
remaining callers do not finish, and the dependencies after it are never
visited. A reserved number is not a finished instance. A construction failure
prints `refused` for the requested name, in the same scope any other refusal of
that request would have used, and immediately after that line we tear down
every instance that finished during the attempt, back to front against
allocation order, even where the owner would have been the root or some other
scope; each `torn` line still names that owner, with the failed request as the
cause, and a singleton caller that never finished still counts when we settle
those owners. Instances that did not finish print nothing. None of these
teardowns runs a parting call. Afterwards nothing the failed attempt built
stays reusable or waits around for a later close. An instance borrowed from
before the attempt keeps its cache entry, its owner and its cause. Earlier
factory tokens survive too, and a failed holder resolution cannot replace them.
The next operation runs normally, a retry after the fault is switched off
included. Allocation numbers are never reused. A factory invocation and each
parting call follow the same failure rules, and a failed parting call finishes
its own cleanup before the close moves on to the next instance.

A component can hold a factory for another registration, and it can invoke that
factory inside a scope that was opened long after the holder itself was built.
Every successful explicit resolution of the holder replaces the tokens for the
factories it declares, even when the holder was already cached or its teardown
belongs somewhere else, and the new token keeps the build scope used for that
resolution. An invocation uses the latest token for that name. Closing the
scope recorded in a token does not cancel it and does not move it; a later
invocation is still charged there, and once that scope has gone it has no
ancestors left in reach. The streams do this more than once against the same
holder, sometimes with a further scope opened and closed in between. A
transient holder behaves no differently from any other holder.

The dump is one sequence and we compare all of it in that order, including
records produced while different scopes are closing. Instance numbers are never
printed, though the order the core allocates them in is what decides teardown
order. The dump has to describe the run that produced it.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
