
We ship a search panel that queries as you type, and it puts rows on screen that belong to
a query the user has already finished typing over. The panel is in /app. The view is passive
and renders whatever the controller pushes at it, so the whole of the defect is in
/app/src/controller.ts.

npm run dev starts the harness on port 5173 with window.__harness in the page, and the short
version of the failure takes four lines. Search c, then ca, then car, and the transport shows
three calls out with requests 1 and 2 marked aborted; answer car first and the panel paints
car, cart, carbon, which is right; then let the reply for c arrive, the one that was already
on the wire when the user typed the second character, and the panel drops to status error
carrying the message The operation was aborted, with the car rows still sitting underneath it.
Nothing failed. The user typed one word and the panel is telling them their search broke.
Short queries are the cheap ones on our backend, so they are the ones that come back late,
and this fires constantly.

The same run shows the other two. Search ca, answer it with cat, car, cape, type on to car,
then backspace to ca, and the call log reads ca, car, ca: the third call goes out for an
answer the first call already brought back. The result field happens not to blank there,
but that is an accident of this ordering. Nothing in the controller filters, and nothing
keeps an answer.

Some ground rules, because a few of them are not what you would do elsewhere.

A settled response may be painted only if it still matches what is in the input at the moment
it tries to write, and aborting the fetch does not decide that for you, since a response can
already be travelling when the query changes and the abort then loses the race and arrives as
an ordinary success with nothing on it to mark it stale, which is why the test belongs at the
write and runs against the query currently being waited for, never against whether anything
was cancelled. Errors are the same. A 500 or a dropped connection moves us to the error state
only when it belongs to the active query, and a superseded request failing in the background
is not an error and must never reach the user.

A query already in flight does not get a second request. When someone backspaces to a query
we hold an authoritative answer for, serve it out of memory, no network call and no spinner,
provisional false and status success. Consider what that has to do to the request still
outstanding, which was issued for a query nobody is now waiting on.

The pane must not go blank while we wait. If car is unresolved and we hold cat, car, cape
for the prefix ca, narrow that to car and show it at once as status loading with provisional
true, then let the authoritative response replace it as success with provisional false when
it lands. Filtered lists are display values. They never go into the cache as answers, and an
empty filtered list while provisional is not the claim that there are no results, because the
server may still return some; result goes to null only when no cached prefix matches at all.

After dispose() runs, late responses and events change nothing: no state writes, no listener
calls, no retained references to a dead component. dispose() called twice, or called before
any search, is a no-op and must not throw.

Subscriber lists get edited while we are walking them, so the meaning of a dispatch has to be
exact. The recipients of an update are those subscribed at the instant the update begins and
all of them receive it, including a subscriber that an earlier listener removed during the
same dispatch, and including a listener that removes itself from inside its own callback,
because the audience is fixed before the first callback runs and delivery does not revise it.
An unsubscribe takes effect on the following update. Someone who subscribes mid-dispatch is
not owed the update in flight and starts with the next one.

Change only /app/src/controller.ts. The other three, /app/src/types.ts, /app/src/transport.ts
and /app/src/main.ts, are hash-checked, so leave them alone, and keep the
createController(transport) export and the QueryState interfaces exactly as they are, because
the harness and the panel both bind to them and a run that cannot construct the controller
through that export scores zero. Run npx tsc --noEmit in /app and keep the types clean.

Responses settle only when you tell them to, so you can build out-of-order arrival directly
instead of waiting on a timer:

    h.reset();                       // fresh controller, cleared transport
    h.controller.search("ca");       // issue a search
    h.transport.pending();           // [{ id, query, aborted }]
    h.transport.settle(1, ["cat"]);  // resolve request 1
    h.transport.fail(1, "boom");     // reject request 1
    h.transport.callLog();           // queries sent, in order
    h.emissions;                     // every state emitted since reset

One more is worth knowing early. h.transport.settleIgnoringAbort(id, items) commits a
response before any cancellation is observed, which is the reply that was already travelling
when the user typed the next character, and it is how cancellation behaves against a real
server, where calling abort tells you nothing about whether the response is already coming.

You have 5400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
