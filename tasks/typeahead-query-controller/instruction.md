
The search panel shows the wrong rows. Everything you need to change is in
/app/src/controller.ts, and the view is passive: it renders whatever state the controller
pushes to it, so the defect is not there.

We issue an HTTP request on every keystroke, c then ca then car, and because short queries
are cheaper on the backend they often come back later than long ones, so the reply for c can
land after the reply for car and the controller paints whichever arrived last. The user reads
results for c with car sitting in the input. Higher latency widens the window.

Two other requirements from the spec were never built. We re-request data we already hold,
and the results pane empties itself every time a new request goes out.

What the panel is supposed to do is below. QA tests against it, so read it as the contract.

Ordering and errors. A settled response may be painted only if it still matches the current
contents of the input, and if the input has since changed you discard it. Cancelling the fetch
does not settle this on its own, because a response can already be on the wire when the query
changes, and the abort then loses the race and arrives as an ordinary success with nothing on
it to mark it stale, which means the test of whether a settled reply may write has to be
applied at the moment it tries to write and against the query currently being waited for,
never against whether anything was cancelled. Errors follow the same rule. A 500 or a
dropped connection moves us into the error state only when it belongs to the active query,
and a superseded request failing in the background is not an error and must never reach the
user.

Deduplication and caching. If a request for car is already in flight, a second search for car
must not open another one. When someone backspaces to a query we already hold an authoritative
answer for, serve it out of memory with no network call and no spinner, provisional false and
status success. Consider what that has to do to the request still outstanding.

Local filtering, so the pane does not go blank. While car is unresolved, if we hold results
for a prefix such as ca, say ["cat", "car", "cape"], narrow them to ["car"] and show that at
once as status loading with provisional true, then let the authoritative response replace it
as success with provisional false when it arrives. Filtered lists are display values. They
must never be written into the cache as answers, and an empty filtered list while provisional
is not the same claim as no results, since the server may still return some. Set result to
null only when no cached prefix matches at all.

Cleanup. After dispose() runs, late responses and events must change nothing: no state
writes, no listener calls, no retained references to a dead component. dispose() called twice,
or called before any search, is a no-op and must not throw.

Subscriber lists get edited while we are walking them, so the meaning of a dispatch needs to
be exact. The recipients of an update are those subscribed at the instant the update begins
and all of them receive it, including a subscriber that an earlier listener removed during
the same dispatch, and including a listener that removes itself from inside its own callback,
because the audience is fixed before the first callback runs and delivery does not revise it.
An unsubscribe takes effect on the following update. A subscriber added mid-dispatch is not
owed the update in flight; it starts with the next one.

Constraints. Change only /app/src/controller.ts. The other three, /app/src/types.ts,
/app/src/transport.ts and /app/src/main.ts, are hash-checked, so leave them alone, and keep
the createController(transport) export and the QueryState interfaces exactly as they are,
because the harness and the panel both bind to them and a run that cannot construct the
controller through that export scores zero. Run npx tsc --noEmit in /app and keep the types
clean.

npm run dev starts the harness on port 5173, and window.__harness is available in the page.
Responses settle only when you tell them to, so you can construct out-of-order arrival
directly instead of waiting on a timer:

    h.reset();                       // fresh controller, cleared transport
    h.controller.search("ca");       // issue a search
    h.transport.pending();           // [{ id, query, aborted }]
    h.transport.settle(1, ["cat"]);  // resolve request 1
    h.transport.fail(1, "boom");     // reject request 1
    h.transport.callLog();           // queries sent, in order
    h.emissions;                     // every state emitted since reset

One more is worth knowing early. h.transport.settleIgnoringAbort(id, items) commits a response
before any cancellation is observed, which is the reply that was already travelling when the
user typed the next character, and it is how cancellation behaves against a real server, where
calling abort tells you nothing about whether the response is already coming.

You have 5400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
