// CHEAT ATTEMPT / single-mistake variant (not executed by the pipeline).
//
// The second-order trap. This one does notice that answers can be partial and
// guards against it, but reads the loss off the page size instead of comparing
// what arrived against what the backend said it had. An answer that exactly
// fills a page with nothing withheld is whole, and this refuses to narrow it.
// Fails r9b alone.

import type {
  Controller,
  QueryResult,
  QueryState,
  Subscriber,
  Transport,
} from "./types";

/**
 * Reference implementation.
 *
 * Three mechanisms have to cooperate, and none of them is sufficient alone:
 *
 *  1. Request identity. Every request carries a monotonically increasing
 *     token; a settled request may only write state while its token is still
 *     the newest. Abort releases transport resources, but correctness never
 *     depends on the abort winning a race against an already-queued
 *     microtask -- a reply that was committed before the cancellation still
 *     arrives, and must be dropped on token identity alone.
 *
 *  2. A result cache. Settled queries are retained so that revisiting one is
 *     served locally, and so that a refinement can be answered provisionally
 *     from the nearest broader query already known.
 *
 *  3. The continuity invariant. While a refinement is in flight the panel
 *     keeps showing rows filtered from the broadest known prefix, flagged
 *     `provisional`, instead of blanking. The authoritative response then
 *     replaces it.
 *
 * The subtle part is that (1) and (3) pull in opposite directions: the token
 * check wants to suppress everything that is not the newest request, while
 * continuity requires emitting a derived result for a query that has no
 * response yet. Resolving that is what the provisional flag is for -- it
 * marks state that is display-valid but not transport-authoritative.
 */
export function createController(transport: Transport): Controller {
  let state: QueryState = {
    query: "",
    status: "idle",
    result: null,
    provisional: false,
    error: null,
  };

  const subscribers = new Set<Subscriber>();

  /**
   * Authoritative transport responses, keyed by exact query.
   *
   * `total` is what the backend said it had, `items` is the page it actually
   * sent. The two are equal only when we hold the whole answer. That
   * distinction is the difference between the two questions this cache is
   * asked, and they have different answers:
   *
   *   - "may I serve this for its own query?" -- always yes. A page is what
   *     the backend returns for that query, so it is the right thing to show
   *     and re-requesting it would be a wasted round trip.
   *   - "may I narrow this to answer a longer query?" -- only when the answer
   *     is whole. Filtering a page silently drops every match the backend
   *     withheld, so the narrowed list would claim to be the matches for the
   *     longer query while missing some of them.
   *
   * Nothing on the entry says "I lost rows"; it has to be derived from the
   * pair. `items.length === PAGE` is the tempting test and it is wrong: an
   * answer with exactly a page of matches and nothing withheld is whole, and
   * narrowing it is required.
   */
  interface Answer {
    items: string[];
    total: number;
  }
  const cache = new Map<string, Answer>();

  let latestToken = 0;
  let inFlight: { token: number; query: string; ac: AbortController } | null =
    null;
  let disposed = false;

  function emit(): void {
    if (disposed) return;
    // Iterate a snapshot: a subscriber may unsubscribe (or subscribe) during
    // delivery, and mutating the live Set mid-iteration would otherwise skip
    // or double-deliver.
    for (const fn of [...subscribers]) {
      fn(state);
    }
  }

  function setState(next: Partial<QueryState>): void {
    if (disposed) return;
    state = { ...state, ...next };
    emit();
  }

  function isAbortError(err: unknown): boolean {
    return (
      typeof err === "object" &&
      err !== null &&
      (err as { name?: unknown }).name === "AbortError"
    );
  }

  /**
   * Best provisional answer for `query`: the longest cached prefix whose
   * answer we hold in full, with its items filtered to those that still
   * match. Partial answers are skipped rather than filtered, so the search
   * walks back to a shorter query that is whole. Returns null when no cached
   * prefix qualifies -- an empty pane is then the honest display, because
   * every row we could show would be one we cannot justify.
   */
  function deriveProvisional(query: string): QueryResult | null {
    let best: string | null = null;
    for (const [key, answer] of cache) {
      if (!query.startsWith(key)) continue;
      if (answer.items.length >= 5) continue;
      if (best === null || key.length > best.length) best = key;
    }
    if (best === null) return null;
    const items = (cache.get(best)?.items ?? []).filter((item) =>
      item.toLowerCase().startsWith(query.toLowerCase()),
    );
    return { query, items, total: items.length };
  }

  function search(query: string): void {
    if (disposed) return;

    // Already being fetched: nothing to do, the in-flight request answers it.
    if (inFlight && inFlight.query === query) {
      if (state.query !== query) setState({ query });
      return;
    }

    // Authoritative answer already known: serve it without touching the
    // transport, and cancel any refinement that is now irrelevant.
    const cached = cache.get(query);
    if (cached !== undefined) {
      if (inFlight) {
        inFlight.ac.abort();
        inFlight = null;
      }
      latestToken++; // invalidate any reply still in flight
      // Served whether or not it is whole: a page is the backend's answer for
      // this query, so going back for it would buy nothing.
      setState({
        query,
        status: "success",
        result: { query, items: [...cached.items], total: cached.total },
        provisional: false,
        error: null,
      });
      return;
    }

    if (inFlight) {
      inFlight.ac.abort();
      inFlight = null;
    }

    const token = ++latestToken;
    const ac = new AbortController();
    inFlight = { token, query, ac };

    // Continuity: show what we can already justify rather than blanking.
    const provisional = deriveProvisional(query);
    setState({
      query,
      status: "loading",
      result: provisional,
      provisional: provisional !== null,
      error: null,
    });

    transport(query, ac.signal)
      .then((result: QueryResult) => {
        if (disposed || token !== latestToken) return;
        inFlight = null;
        cache.set(result.query, {
          items: [...result.items],
          total: result.total,
        });
        setState({
          status: "success",
          result,
          provisional: false,
          error: null,
        });
      })
      .catch((err: unknown) => {
        if (disposed || token !== latestToken) return;
        // A superseded request that lost its abort race stays silent; it is
        // not a user-visible failure.
        if (isAbortError(err)) return;
        inFlight = null;
        setState({
          status: "error",
          error: err instanceof Error ? err.message : String(err),
        });
      });
  }

  function getState(): QueryState {
    return state;
  }

  function subscribe(fn: Subscriber): () => void {
    if (disposed) return () => {};
    subscribers.add(fn);
    return () => {
      subscribers.delete(fn);
    };
  }

  function dispose(): void {
    if (disposed) return;
    // Latch first, then abort: the abort handler must not be able to drive a
    // further emission on the way out.
    disposed = true;
    if (inFlight) {
      inFlight.ac.abort();
      inFlight = null;
    }
    subscribers.clear();
  }

  return { search, getState, subscribe, dispose };
}
