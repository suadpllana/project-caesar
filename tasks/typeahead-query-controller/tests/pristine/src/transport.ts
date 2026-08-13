import type { QueryResult, Transport } from "./types";

/**
 * Test transport.
 *
 * Requests do not resolve on their own: each call registers a pending entry
 * and waits until the driver settles it by id. This makes response ordering
 * fully controllable, so out-of-order arrival can be reproduced exactly
 * rather than by racing real timers.
 *
 * Do not modify this file. The conformance suite drives the controller
 * through this exact interface.
 */

interface Pending {
  id: number;
  query: string;
  resolve: (r: QueryResult) => void;
  reject: (e: unknown) => void;
  aborted: boolean;
  /** Once committed, an abort no longer rejects this request. */
  committed: boolean;
  /** Set once the promise has actually been settled. */
  done: boolean;
}

export interface TransportHandle {
  transport: Transport;
  /** Ids of requests that have been started and not yet settled. */
  pending(): { id: number; query: string; aborted: boolean }[];
  /** Total number of transport invocations since reset. */
  callCount(): number;
  /** Queries passed to the transport, in invocation order. */
  callLog(): string[];
  /** Settle a pending request successfully. */
  settle(id: number, items: string[]): void;
  /** Settle a pending request with a failure. */
  fail(id: number, message: string): void;
  /**
   * Commit a response *before* any abort is observed, modelling a reply that
   * is already in the microtask queue when the caller cancels. The request
   * resolves successfully even if it is aborted afterwards -- exactly the
   * window in which a cancellation loses the race to an arriving response.
   */
  settleIgnoringAbort(id: number, items: string[]): void;
  reset(): void;
}

export function createTransport(): TransportHandle {
  let nextId = 1;
  let pendings: Pending[] = [];
  let log: string[] = [];

  const transport: Transport = (query, signal) => {
    const id = nextId++;
    log.push(query);

    return new Promise<QueryResult>((resolve, reject) => {
      const entry: Pending = {
        id,
        query,
        resolve,
        reject,
        aborted: false,
        committed: false,
        done: false,
      };
      pendings.push(entry);

      const onAbort = (): void => {
        entry.aborted = true;
        // A committed response has already left the server; cancelling now
        // is too late to stop it.
        if (entry.committed || entry.done) return;
        entry.done = true;
        reject(makeAbortError());
      };

      if (signal.aborted) {
        onAbort();
        return;
      }

      signal.addEventListener("abort", onAbort);
    });
  };

  function makeAbortError(): Error {
    // DOMException is available in the browser; name must be "AbortError".
    const err = new DOMException("The operation was aborted.", "AbortError");
    return err as unknown as Error;
  }

  function take(id: number): Pending | undefined {
    const found = pendings.find((p) => p.id === id);
    if (found) {
      pendings = pendings.filter((p) => p.id !== id);
    }
    return found;
  }

  return {
    transport,
    pending: () =>
      pendings.map((p) => ({ id: p.id, query: p.query, aborted: p.aborted })),
    callCount: () => log.length,
    callLog: () => [...log],
    settle: (id, items) => {
      const p = take(id);
      if (p && !p.done) {
        p.done = true;
        p.resolve({ query: p.query, items });
      }
    },
    fail: (id, message) => {
      const p = take(id);
      if (p && !p.done) {
        p.done = true;
        p.reject(new Error(message));
      }
    },
    settleIgnoringAbort: (id, items) => {
      const p = pendings.find((x) => x.id === id);
      if (!p) return;
      p.committed = true;
      if (p.done) return;
      p.done = true;
      pendings = pendings.filter((x) => x.id !== id);
      p.resolve({ query: p.query, items });
    },
    reset: () => {
      nextId = 1;
      pendings = [];
      log = [];
    },
  };
}
