/**
 * Public contract for the query controller.
 *
 * These types are fixed. Do not change them: the conformance suite and the
 * host application both depend on these exact shapes.
 */

export interface QueryResult {
  /** The query string this result corresponds to. */
  query: string;
  /** Matching items, in the order returned by the transport. */
  items: string[];
}

export type QueryStatus = "idle" | "loading" | "success" | "error";

export interface QueryState {
  /** The query string most recently requested by the caller. */
  query: string;
  status: QueryStatus;
  /**
   * The result currently displayed. Must always correspond to the most
   * recently *settled* query that is still relevant -- never to a query the
   * caller has since superseded.
   */
  result: QueryResult | null;
  /**
   * True when `result` was derived locally from a broader query rather than
   * returned by the transport for exactly `query`. Lets the view show the
   * rows it already has while a refinement is still in flight.
   */
  provisional: boolean;
  /** Populated only when status === "error". */
  error: string | null;
}

/**
 * A transport performs a single search request.
 *
 * The `signal` is provided so implementations can abort in-flight work. A
 * transport that is aborted rejects with a DOMException whose name is
 * "AbortError".
 */
export type Transport = (
  query: string,
  signal: AbortSignal,
) => Promise<QueryResult>;

export type Subscriber = (state: QueryState) => void;

export interface Controller {
  /** Request results for `query`. Safe to call at any rate. */
  search(query: string): void;
  /** Current state. Never throws. */
  getState(): QueryState;
  /** Subscribe to state changes. Returns an unsubscribe function. */
  subscribe(fn: Subscriber): () => void;
  /**
   * Permanently shut down the controller: abort in-flight work and stop
   * emitting. Idempotent.
   */
  dispose(): void;
}
