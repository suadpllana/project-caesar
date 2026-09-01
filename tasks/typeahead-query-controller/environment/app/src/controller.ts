import type {
  Controller,
  QueryResult,
  QueryState,
  Subscriber,
  Transport,
} from "./types";

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
