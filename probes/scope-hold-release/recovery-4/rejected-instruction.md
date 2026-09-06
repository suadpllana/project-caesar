`/app` is the container our services are wired through. Registrations name a
lifetime, scopes open and close around a unit of work, and when a scope closes
the container tears down whatever belongs to it. We rewrote the ownership and
teardown decisions last cycle and it has been wrong since.

Run `/app/run_wire.py` on `/app/cases/wide.txt`. The third line back reads
`torn pool 1 app`, and that line should not exist. `pool` was pulled in
underneath `app`, a singleton that outlives every scope in that stream.
Closing scope 1 has disposed of a dependency the live singleton is still
holding. There are nine more case files in `/app/cases`. None of them comes
out right either.

`/app/wire/own.py`, `/app/wire/pin.py`, `/app/wire/hold.py`, `/app/wire/gate.py`,
`/app/wire/tear.py`, `/app/wire/shut.py` and `/app/wire/plan.py` are yours to
change. Some of them are right. `/app/wire/core.py`, `/app/wire/reg.py` and
`/app/wire/scope.py` are the container itself and you may not touch them.
Read them anyway. They already settle things the editable files have to
agree with.

We grade the dump, line for line, in the order it comes out. A teardown is
`torn NAME OWNER CAUSE`: the registration name, the scope that owned the
instance, and the name requested when it was built. A dependency's cause is
the name at the top of the resolution, not its immediate parent. A declined
resolution is `refused NAME SCOPE`. These are the only two record kinds.
Write refusals when they happen, not at the end. A refused invoke names the
scope where it was attempted; a refused parting call names the scope where
it had to land. Other refusals name the current scope. Instance numbers are
not printed.

An instance belongs to the scope the work was charged to unless one of the
rules below moves it. A singleton is built once and is owned by the root;
everything it pulls in belongs to the root too, however deep the chain runs
and whatever lifetime or mark those dependencies declare for themselves;
that rule wins over the mark. Finding an instance already built changes
neither its owner nor its cause. A scoped registration is reused by
registration and build scope.

Within a scope, teardown runs back to front against allocation order. The
core sets aside an instance number before it goes on to build dependencies
or a wrapped registration. Those later allocations are torn down first.
Closing a scope tears down nothing an ancestor owns. A scope that owns
nothing closes silently. The root itself never closes.

A registration can carry a mark. Outside a singleton's chain, one that does
is owned by the nearest scope in reach carrying the same mark, starting from
the scope the work was charged to and walking through its ancestors. With
no matching scope in reach, its owner is the root.
The mark moves that instance only. Its dependencies keep their own ownership
rules, and neither its build scope nor its cache key moves with it.

A registration can also wrap another or declare a parting call. The parting
call resolves a name straight after the instance's `torn` line. It is charged
to the scope outside the one that is closing, because nothing may be built
into the closing scope any more.

Admission belongs to the name we were asked for. We refuse a requested
singleton that can reach a scoped registration through dependencies or
wrapping, at any depth. We also refuse a requested marked registration when
no scope in reach carries its mark. Those two checks stop at the request;
they are not started again for every name pulled in underneath it. Cycle
detection does keep going: a dependency or wrapping cycle anywhere below
the requested name refuses the whole request. Failing admission builds
nothing at all.

We also refuse a parting call that cannot be resolved where it has to land,
a close with no scope open, and invoking a factory whose holder has not
been resolved yet. Each produces a `refused` line and nothing else. Every
name in the streams is registered. A factory declaration is not a dependency.

Construction can fail after admission. The optional last field on a
registration line, after its parting-call name, is `fail`; missing it or
writing `.` means the constructor starts available. `o fault NAME on`
makes that constructor unavailable and `o fault NAME off` restores it.
These operations print nothing and do not change a registration or dispose
of an instance already built.

A cached instance is still usable while its constructor is unavailable.
Otherwise the wrapped registration is built first, then dependencies in
their listed order, and only then does this constructor run and fail if it
is unavailable. Its remaining callers do not finish and later dependencies
are not visited.

A construction failure prints `refused` for the requested name, using the
same scope as any other refusal of that request. Immediately after it,
tear down every instance that finished during that attempt, back to front
against allocation order, even if its owner would have been the root or
another scope. Each `torn` line still names that owner and the failed
request as cause. The ownership rules include singleton callers that never
finished. An allocation whose constructor did not finish produces no
teardown record. These teardowns do not run parting calls.

Afterwards, nothing built by the failed attempt remains reusable or waits
for a later scope close. An instance borrowed from before the attempt keeps
its cache entry, owner and cause. Earlier factory bindings survive too; a
failed holder resolution cannot replace them. The next operation runs
normally, including a retry after a fault is turned off. Allocation numbers
are not reused. A factory invocation and each parting call follow the same
failure rules. A failed parting call finishes its cleanup before the scope
close goes on to the next instance.

A component can hold a factory for another registration, and it can invoke
that factory inside a scope that was opened after the holder itself was
built. Every successful explicit resolution of the holder replaces the
tokens for the factories it declares, even when the holder was already
cached or its teardown belongs somewhere else, and the new token keeps the
build scope used for that resolution. An invocation uses the latest token
for that factory name. Closing the scope recorded in a token does not
cancel it or move it; a later invocation is still charged there, and once
that scope has gone it has no ancestors in reach. The streams do this more
than once against the same holder, sometimes with a further scope opened and
closed in between. A transient holder behaves no differently from any other
holder.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
