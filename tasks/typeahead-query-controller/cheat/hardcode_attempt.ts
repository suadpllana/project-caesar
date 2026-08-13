import type {
  Controller,
  QueryResult,
  QueryState,
  Subscriber,
  Transport,
} from "./types";

/**
 * CHEAT ATTEMPT (not executed by the pipeline).
 *
 * Pretend to implement the contract by recognising the fixture strings and
 * replaying canned answers, without any real cache or continuity logic.
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
  let latest = 0;
  let disposed = false;

  const CANNED: Record<string, string[]> = {
    ca: ["cat"],
    car: ["car"],
  };

  function emit(): void {
    if (disposed) return;
    for (const fn of [...subscribers]) fn(state);
  }
  function setState(n: Partial<QueryState>): void {
    if (disposed) return;
    state = { ...state, ...n };
    emit();
  }

  function search(query: string): void {
    if (disposed) return;
    const canned = CANNED[query];
    if (canned) {
      setState({
        query,
        status: "success",
        result: { query, items: [...canned] },
        provisional: false,
        error: null,
      });
      return;
    }
    const token = ++latest;
    const ac = new AbortController();
    setState({ query, status: "loading", result: null, provisional: false });
    transport(query, ac.signal)
      .then((r: QueryResult) => {
        if (disposed || token !== latest) return;
        setState({ status: "success", result: r, provisional: false });
      })
      .catch(() => {});
  }

  return {
    search,
    getState: () => state,
    subscribe: (fn) => {
      subscribers.add(fn);
      return () => {
        subscribers.delete(fn);
      };
    },
    dispose: () => {
      disposed = true;
      subscribers.clear();
    },
  };
}
