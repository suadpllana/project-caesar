import type {
  Controller,
  QueryResult,
  QueryState,
  Subscriber,
  Transport,
} from "./types";

/**
 * Search controller used by the type-ahead panel.
 *
 * Known issue (INC-2231): under fast typing the panel intermittently shows
 * results belonging to an earlier keystroke, and the spinner sometimes stays
 * up after the last request has settled. Reproduces most easily when the
 * network is slow and responses arrive out of order.
 *
 * The result cache and the provisional-display behaviour described in the
 * panel spec were never implemented here: every keystroke goes to the
 * transport, and the pane blanks while it waits.
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
  let inFlight: AbortController | null = null;

  function emit(): void {
    for (const fn of subscribers) {
      fn(state);
    }
  }

  function setState(next: Partial<QueryState>): void {
    state = { ...state, ...next };
    emit();
  }

  function search(query: string): void {
    if (inFlight) {
      inFlight.abort();
    }

    const ac = new AbortController();
    inFlight = ac;

    setState({ query, status: "loading" });

    transport(query, ac.signal)
      .then((result: QueryResult) => {
        setState({ status: "success", result, error: null });
      })
      .catch((err: unknown) => {
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
    subscribers.add(fn);
    return () => {
      subscribers.delete(fn);
    };
  }

  function dispose(): void {
    if (inFlight) {
      inFlight.abort();
    }
    subscribers.clear();
  }

  return { search, getState, subscribe, dispose };
}
