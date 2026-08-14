/**
 * Conformance scenarios, executed inside the page against the agent's
 * controller via window.__harness.
 *
 * Each scenario is a function body evaluated in the browser. It returns a
 * plain JSON-serialisable verdict object: { pass: boolean, detail: string }.
 *
 * These run against the real module graph served by Vite, so the agent's
 * actual source is under test -- not a re-implementation.
 */

/**
 * Prelude injected before every scenario body.
 *
 * The harness is taken from the module namespace of main.ts, never from
 * window.__harness. main.ts is hashed against the pristine copy, and a module
 * namespace object is sealed, so no other module in the graph can substitute
 * what `h` refers to. A global rendezvous point could be pre-empted: every
 * scenario reaches the app through this one binding, and controller.ts is
 * evaluated (as an import of main.ts) before main.ts assigns anything to
 * window, so an accessor installed there would capture the whole suite.
 * `import()` is syntax rather than a global lookup, so it cannot be patched
 * out from inside the graph either.
 *
 * `need(q)` returns the id of the pending request for `q`, or throws a
 * BadState carrying a readable message. The driver turns that into an
 * ordinary failing verdict rather than an opaque TypeError, so a controller
 * that simply never issues a request reports why instead of crashing.
 */
const PRELUDE = `
  const h = (await import("/src/main.ts")).harness;
  if (!h || typeof h.reset !== "function") {
    throw new Error("main.ts did not export a usable harness");
  }
  class BadState extends Error {
    constructor(m) { super(m); this.name = "BadState"; }
  }
  const need = (q) => {
    const p = h.transport.pending().find((x) => x.query === q);
    if (!p) throw new BadState("no in-flight transport request for [" + q + "]");
    return p.id;
  };
`;

const SCENARIOS = [
  {
    id: "r1_ordering_committed_stale",
    title: "a reply committed before cancellation is never displayed",
    body: `
      h.reset();
      const bad = [];
      h.controller.subscribe((s) => {
        if (s.result && !s.provisional && s.result.query !== s.query) {
          bad.push(s.query + "<-" + s.result.query);
        }
      });
      h.controller.search("a");
      await tick();
      h.transport.settleIgnoringAbort(need("a"), ["A"]);
      h.controller.search("ab");
      await tick();
      const idAB = h.transport.pending().find(p => p.query === "ab");
      if (idAB) h.transport.settle(idAB.id, ["AB"]);
      await tick();
      const s = h.controller.getState();
      const finalOk = s.result === null || s.result.query === "ab";
      return {
        pass: bad.length === 0 && finalOk,
        detail: "staleEmissions=[" + bad.join(",") + "] final=" +
                (s.result ? s.result.query : "none"),
      };
    `,
  },
  {
    id: "r1b_ordering_out_of_order_settle",
    title: "an older reply landing after a newer one does not overwrite it",
    body: `
      h.reset();
      h.controller.search("x");
      await tick();
      h.transport.settleIgnoringAbort(need("x"), ["OLD"]);
      h.controller.search("xy");
      await tick();
      const idXY = h.transport.pending().find(p => p.query === "xy");
      if (idXY) h.transport.settle(idXY.id, ["NEW"]);
      await tick();
      const s = h.controller.getState();
      return {
        pass: s.status === "success" && s.result &&
              s.result.query === "xy" && s.result.items.join() === "NEW",
        detail: "status=" + s.status + " shown=" +
                (s.result ? s.result.query + ":" + s.result.items.join("|") : "none"),
      };
    `,
  },
  {
    id: "r2_abort_not_surfaced",
    title: "cancelling a superseded request raises no user-visible error",
    body: `
      h.reset();
      h.controller.search("a");
      await tick();
      h.controller.search("ab");
      await tick();
      const s = h.controller.getState();
      return {
        pass: s.status !== "error" && s.error === null,
        detail: "status=" + s.status + " error=" + String(s.error),
      };
    `,
  },
  {
    id: "r3_coalesce_in_flight",
    title: "repeating the in-flight query does not re-hit the transport",
    body: `
      h.reset();
      h.controller.search("a");
      h.controller.search("a");
      h.controller.search("a");
      await tick();
      return {
        pass: h.transport.callCount() === 1,
        detail: "calls=" + h.transport.callCount() +
                " log=" + h.transport.callLog().join(","),
      };
    `,
  },
  {
    id: "r4_continuity_provisional",
    title: "narrowing keeps a filtered result on screen instead of blanking",
    body: `
      h.reset();
      h.controller.search("ca");
      await tick();
      h.transport.settle(need("ca"), ["cat","car","cape"]);
      await tick();
      const blanked = [];
      h.controller.subscribe((s) => {
        if (s.status === "loading" && s.result === null) blanked.push(s.query);
      });
      h.controller.search("car");
      await tick();
      const s = h.controller.getState();
      const items = s.result ? s.result.items.join("|") : "none";
      return {
        pass: blanked.length === 0 && s.result !== null &&
              s.provisional === true && items === "car",
        detail: "blanked=[" + blanked.join(",") + "] shown=" + items +
                " provisional=" + String(s.provisional),
      };
    `,
  },
  {
    id: "r4b_provisional_replaced_by_authoritative",
    title: "the authoritative reply replaces the provisional rows",
    body: `
      h.reset();
      h.controller.search("ca");
      await tick();
      h.transport.settle(need("ca"), ["cat","car","cape"]);
      await tick();
      h.controller.search("car");
      await tick();
      h.transport.settle(need("car"), ["car","cargo"]);
      await tick();
      const s = h.controller.getState();
      return {
        pass: s.status === "success" && s.provisional === false &&
              s.result && s.result.items.join("|") === "car|cargo",
        detail: "status=" + s.status + " provisional=" + String(s.provisional) +
                " shown=" + (s.result ? s.result.items.join("|") : "none"),
      };
    `,
  },
  {
    id: "r5_cache_revisit",
    title: "revisiting a settled query is served without a request",
    body: `
      h.reset();
      h.controller.search("ca");
      await tick();
      h.transport.settle(need("ca"), ["cat"]);
      await tick();
      h.controller.search("do");
      await tick();
      h.transport.settle(need("do"), ["dog"]);
      await tick();
      const before = h.transport.callCount();
      h.controller.search("ca");
      await tick();
      const s = h.controller.getState();
      return {
        pass: h.transport.callCount() === before && s.status === "success" &&
              s.provisional === false &&
              s.result && s.result.query === "ca" &&
              s.result.items.join("|") === "cat",
        detail: "callsBefore=" + before + " callsAfter=" + h.transport.callCount() +
                " status=" + s.status + " shown=" +
                (s.result ? s.result.query + ":" + s.result.items.join("|") : "none"),
      };
    `,
  },
  {
    id: "r6_dispose_latch",
    title: "a reply arriving after dispose mutates nothing",
    body: `
      h.reset();
      h.controller.search("a");
      await tick();
      const before = JSON.stringify(h.controller.getState());
      const p = h.transport.pending()[0];
      h.controller.dispose();
      if (p) h.transport.settleIgnoringAbort(p.id, ["LATE"]);
      await tick();
      const after = JSON.stringify(h.controller.getState());
      return {
        pass: before === after,
        detail: before === after ? "unchanged" : ("before=" + before + " after=" + after),
      };
    `,
  },
  {
    id: "r6b_dispose_idempotent",
    title: "dispose is idempotent and stops emissions",
    body: `
      h.reset();
      let hits = 0;
      h.controller.subscribe(() => hits++);
      h.controller.search("a");
      await tick();
      const atDispose = hits;
      h.controller.dispose();
      h.controller.dispose();
      h.controller.search("b");
      await tick();
      return {
        pass: hits === atDispose,
        detail: "hitsAtDispose=" + atDispose + " hitsAfter=" + hits,
      };
    `,
  },
  {
    id: "r7_emit_snapshot",
    title: "a subscriber removed by a peer mid-dispatch still receives that update",
    body: `
      h.reset();
      // Peer-removal only: the first listener removes two others, and never
      // itself. An implementation that re-reads the live subscriber set
      // between callbacks skips them here. r7c covers self-removal, which
      // this scenario cannot distinguish.
      const hits = [0,0,0,0];
      const offs = [];
      offs.push(h.controller.subscribe(() => {
        hits[0]++;
        if (offs[1]) offs[1]();
        if (offs[2]) offs[2]();
      }));
      offs.push(h.controller.subscribe(() => hits[1]++));
      offs.push(h.controller.subscribe(() => hits[2]++));
      offs.push(h.controller.subscribe(() => hits[3]++));
      h.controller.search("a");
      await tick();
      return {
        pass: hits[0] === 1 && hits[1] === 1 && hits[2] === 1 && hits[3] === 1,
        detail: "hits=" + hits.join(","),
      };
    `,
  },
  {
    id: "r7c_self_unsubscribe_during_delivery",
    title: "a listener that unsubscribes itself still receives that update",
    body: `
      h.reset();
      // Self-removal only, which r7 cannot separate from peer-removal: an
      // implementation that walks a snapshot and one that removes the
      // current listener before calling it both pass r7, and only this
      // scenario tells them apart. It also pins the joining side: a
      // subscriber registered from inside a callback is not owed the
      // dispatch already under way.
      const self = [0, 0];
      const late = [0];
      const off0 = h.controller.subscribe(() => {
        self[0]++;
        off0();
        h.controller.subscribe(() => late[0]++);
      });
      h.controller.subscribe(() => self[1]++);
      h.controller.search("a");
      await tick();
      const firstOk = self[0] === 1 && self[1] === 1 && late[0] === 0;
      h.transport.settle(need("a"), ["ant"]);
      await tick();
      const secondOk = self[0] === 1 && self[1] === 2 && late[0] === 1;
      return {
        pass: firstOk && secondOk,
        detail: "self=" + self.join(",") + " late=" + late[0] +
                " firstOk=" + firstOk + " secondOk=" + secondOk,
      };
    `,
  },
  {
    id: "r7b_real_error_surfaces",
    title: "a genuine transport failure is still reported",
    body: `
      h.reset();
      h.controller.search("a");
      await tick();
      h.transport.fail(need("a"), "boom");
      await tick();
      const s = h.controller.getState();
      return {
        pass: s.status === "error" && s.error === "boom",
        detail: "status=" + s.status + " error=" + String(s.error),
      };
    `,
  },
  {
    id: "r8_burst_typing",
    title: "a long burst settles on the final query with matching payload",
    body: `
      h.reset();
      const mismatches = [];
      h.controller.subscribe((s) => {
        if (s.status === "success" && s.result && s.result.query !== s.query) {
          mismatches.push(s.query + "<-" + s.result.query);
        }
      });
      const steps = ["c","ca","car","carb","carbo","carbon"];
      for (const q of steps) {
        h.controller.search(q);
        await tick();
        // Commit every reply irrevocably before the next keystroke, so each
        // one is racing the cancellation that is about to follow.
        const p = h.transport.pending().find(x => x.query === q);
        if (p) h.transport.settleIgnoringAbort(p.id, [q.toUpperCase()]);
      }
      await tick();
      await tick();
      const s = h.controller.getState();
      return {
        pass: mismatches.length === 0 && s.query === "carbon" &&
              s.status === "success" && s.result &&
              s.result.query === "carbon",
        detail: "mismatches=[" + mismatches.join(",") + "] finalQuery=" + s.query +
                " status=" + s.status + " shown=" +
                (s.result ? s.result.query : "none"),
      };
    `,
  },
];

module.exports = { SCENARIOS, PRELUDE };
