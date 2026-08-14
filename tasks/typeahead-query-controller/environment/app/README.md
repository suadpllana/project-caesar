# Type-ahead panel

The panel issues a search on every keystroke and renders whatever the
controller currently holds. All of the interesting behaviour lives in
`src/controller.ts`; the view is deliberately dumb.

## Product spec

These are the rules the panel is supposed to follow. They were agreed with
design after the first round of complaints about the results "jumping
around", and are what QA tests against.

1. **What you see matches what you typed.** The rows on screen always belong
   to the query the user most recently asked for. If they have typed past a
   query, its results are dead -- they must never be displayed, not even for
   a frame on the way to being replaced.

2. **Cancelling is invisible.** Superseding a search is a normal thing to do
   and is never reported to the user as a failure. A search that genuinely
   fails *is* reported, with the transport's message.

3. **Don't ask twice.** Re-requesting something already in flight, or
   something already fetched, must not generate another request. Backspacing
   to a query that was already run is served from what we have.

4. **The pane doesn't flash empty.** While waiting for a refinement, keep
   showing what we can already justify: the rows from the nearest broader
   query we know about, narrowed to those still matching what has been
   typed. Those rows are marked `provisional: true` and `status` stays
   `"loading"` until the real response arrives and replaces them with
   `provisional: false`.

   If we know nothing relevant, `result` is `null` and the pane is empty --
   that is correct, not a bug.

5. **Teardown is final.** Once `dispose()` has been called the controller is
   inert: no further emissions, no further state changes, whatever arrives
   late. Calling it more than once is harmless.

6. **The audience for an update is fixed before it is delivered.** Every
   subscriber registered at the moment an update begins receives that
   update, and nothing that happens during delivery revises the list. A
   subscriber that a peer unsubscribes partway through the dispatch still
   receives it. A subscriber that unsubscribes itself from inside its own
   callback has already received it. Either way the unsubscribe takes
   effect from the next update onwards. A subscriber that registers during
   delivery is not owed the update in flight and starts with the next one.

## Known issue

INC-2231. Under fast typing the panel intermittently shows results from an
earlier keystroke, and the spinner sometimes stays up after the last request
has settled. Reproduces most easily on a slow connection, where responses
arrive out of order.

Rules 3 and 4 were never implemented at all: every keystroke goes to the
transport, and the pane blanks while it waits.

## Development

```sh
npm run dev        # serves on http://localhost:5173
npx tsc --noEmit   # type-check
```

### Driving it by hand

`window.__harness` is available in the page:

```js
const h = window.__harness;
h.reset();                       // fresh controller, cleared transport
h.controller.search("ca");       // issue a search
h.transport.pending();           // [{ id, query, aborted }]
h.transport.settle(1, ["cat"]);  // resolve request 1
h.transport.fail(1, "boom");     // reject request 1
h.transport.callLog();           // queries sent, in order
h.emissions;                     // every state emitted since reset
```

Responses only settle when you say so, so out-of-order arrival can be set up
deliberately instead of waited for.

`h.transport.settleIgnoringAbort(id, items)` commits a response *before* any
cancellation is observed -- the reply was already on the wire when the user
typed the next character. Cancellation is genuinely lossy here, exactly as it
is against a real server: aborting does not guarantee the response is not
already coming.

## Files

| File | |
| --- | --- |
| `src/controller.ts` | the controller — **the only file you should change** |
| `src/types.ts` | shared contract — do not modify |
| `src/transport.ts` | test transport — do not modify |
| `src/main.ts` | harness + view wiring — do not modify |
