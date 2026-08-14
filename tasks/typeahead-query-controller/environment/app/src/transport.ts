import type { QueryResult, Transport } from "./types";

interface Pending {
  id: number;
  query: string;
  resolve: (r: QueryResult) => void;
  reject: (e: unknown) => void;
  aborted: boolean;
  committed: boolean;
  done: boolean;
}

export interface TransportHandle {
  transport: Transport;
  pending(): { id: number; query: string; aborted: boolean }[];
  callCount(): number;
  callLog(): string[];
  settle(id: number, items: string[]): void;
  fail(id: number, message: string): void;
  settleIgnoringAbort(id: number, items: string[]): void;
  reset(): void;
}

const PAGE = 5;

export function createTransport(): TransportHandle {
  let nextId = 1;
  let pendings: Pending[] = [];
  let log: string[] = [];

  function page(query: string, matches: string[]): QueryResult {
    return { query, items: matches.slice(0, PAGE), total: matches.length };
  }

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
        p.resolve(page(p.query, items));
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
      p.resolve(page(p.query, items));
    },
    reset: () => {
      nextId = 1;
      pendings = [];
      log = [];
    },
  };
}
