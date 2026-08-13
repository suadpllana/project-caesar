
Everything you need to touch lives in /app/src/controller.ts. The view's totally dumb, it just renders whatever the controller pushes to it.

Here's the actual bug: we fire an HTTP request on every keystroke (c, then ca, then car), and since shorter queries tend to take longer on the backend, the response for c can land after the response for car. The controller just paints whatever arrives last, so you end up staring at car in the box while it shows results for c. Gets worse the higher the latency.

On top of that, a couple things from the spec never got built: we're re-fetching data we already have, and the results pane blanks out every time it's waiting on a new response.

Here is what the panel is supposed to do. QA tests against these, so treat them as the contract:

Out-of-order responses & errors
Only paint a response if it still matches what's in the input box. If the user's moved on, just drop it, no fuss. Aborting the fetch isn't enough on its own either, since a response can already be in flight when the query changes and the abort then loses its race, arriving as a perfectly ordinary success that no signal ever flagged, which means the decision about whether a settled reply may write anything has to be made at the moment it tries to write and on the basis of whether it is still the one being waited for, not on whether anybody remembered to cancel it. And errors (500s, network failures) should only flip us into an "error" state if they happen on the active query. A superseded request dying in the background shouldn't cause any error or flicker.

Dedup & caching
Don't fire a second request for car if one's already in flight. And if someone backspaces back to a query we already have a solid answer for, pull it from memory instantly, no network call, no spinner, provisional: false, status "success". Watch what that does to the request still outstanding.

Local filtering (so the pane doesn't go blank)
While car is still resolving, if we've got results cached for a prefix like ca (say ["cat", "car", "cape"]), filter it down to ["car"] and show that immediately. That state should read status: "loading", provisional: true. Once the real response comes back, swap it over to "success" / provisional: false. Don't ever write provisional/filtered lists into the cache as if they were real answers. Also, an empty filtered list while still provisional isn't the same as "no results," since the server might still find something. Only set result: null if there's no matching prefix at all.

Cleanup
Once dispose() runs, any late network responses or events should just get ignored: no state updates, no listener calls, no hanging refs to dead components. Calling dispose() more than once, or before any query's even been made, should be a total no-op, no throwing.

Subscriber lists get edited while we're walking them. Pin down what a dispatch means: the recipients of an update are whoever is subscribed at the instant that update starts going out, and every one of them gets it, including a subscriber that some earlier listener unsubscribed halfway through the dispatch, and including a listener that unsubscribed itself from inside its own callback, because the audience is settled before the first callback runs and nothing that happens during delivery revises it. An unsubscribe bites on the next update. Someone who subscribes mid-dispatch is not owed the one in flight. They start with the following one.

Constraints
Only touch /app/src/controller.ts. /app/src/types.ts, /app/src/transport.ts, and /app/src/main.ts are hash-checked, hands off. Keep the createController(transport) export and the QueryState interfaces as-is, since the harness and the panel both bind to them and a run that cannot construct the controller through that export scores nothing at all. Run npx tsc --noEmit in /app. Types have to be clean.

npm run dev spins up the harness on port 5173. window.__harness is in the page. Responses only settle when you say so, so you set up out-of-order arrival deliberately instead of waiting on a timer and hoping:

    h.reset();                       // fresh controller, cleared transport
    h.controller.search("ca");       // issue a search
    h.transport.pending();           // [{ id, query, aborted }]
    h.transport.settle(1, ["cat"]);  // resolve request 1
    h.transport.fail(1, "boom");     // reject request 1
    h.transport.callLog();           // queries sent, in order
    h.emissions;                     // every state emitted since reset

One more matters. h.transport.settleIgnoringAbort(id, items) commits a response before any cancellation is observed, which models the reply that was already on the wire when the user typed the next character, and it is worth playing with early because cancellation here is lossy in exactly the way it is against a real server: calling abort buys you nothing about whether the response is already coming.

You have 5400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
