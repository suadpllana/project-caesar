
Everything I need to touch lives in /app/src/controller.ts. The view's totally dumb, it just renders whatever the controller pushes to it.

Here's the actual bug: we fire an HTTP request on every keystroke (c → ca → car), and since shorter queries tend to take longer on the backend, the response for c can land after the response for car. The controller just paints whatever arrives last, so you end up staring at car in the box while it shows results for c. Gets worse the higher the latency.

On top of that, a couple things from the spec never got built: we're re-fetching data we already have, and the results pane blanks out every time it's waiting on a new response.

/app/README.md is the source of truth for how this thing should behave. A few things it needs to cover:

Out-of-order responses & errors
Only paint a response if it still matches what's in the input box. If the user's moved on, just drop it, no fuss. Aborting the fetch isn't enough on its own either, since a response can already be in flight when the query changes, so its resolution needs to be a no-op in that case. And errors (500s, network failures) should only flip us into an "error" state if they happen on the active query. A superseded request dying in the background shouldn't cause any error or flicker.

Dedup & caching
Don't fire a second request for car if one's already in flight. And if someone backspaces back to a query we already have a solid answer for, pull it from memory instantly, no network call, no spinner, provisional: false, status "success".

Local filtering (so the pane doesn't go blank)
While car is still resolving, if we've got results cached for a prefix like ca (say ["cat", "car", "cape"]), filter it down to ["car"] and show that immediately. That state should read status: "loading", provisional: true. Once the real response comes back, swap it over to "success" / provisional: false. Don't ever write provisional/filtered lists into the cache as if they were real answers. Also, an empty filtered list while still provisional isn't the same as "no results," since the server might still find something. Only set result: null if there's no matching prefix at all.

Cleanup
Once dispose() runs, any late network responses or events should just get ignored: no state updates, no listener calls, no hanging refs to dead components. Calling dispose() more than once, or before any query's even been made, should be a total no-op, no throwing.

Notifying subscribers
This one needs saying exactly, because we edit the subscriber list while we're walking it and the loose version of the rule doesn't decide the cases QA actually files. Every subscriber present when an update begins receives that update, even if a peer unsubscribes it during that dispatch, and even if it unsubscribes itself from inside its own callback. An unsubscribe takes effect on the following update, never on the one being delivered. Someone who subscribes mid-dispatch isn't owed the update in flight and starts with the next one.

Constraints
Only touch /app/src/controller.ts. /app/src/types.ts, /app/src/transport.ts, and /app/src/main.ts are hash-checked, hands off. Keep the createController(transport) export and the QueryState interfaces as-is. Run npx tsc --noEmit in /app to make sure types are clean.

npm run dev spins up the harness on port 5173, and window.__harness lets you manually settle pending requests out of order so you can actually verify the fix works.

You have 5400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
