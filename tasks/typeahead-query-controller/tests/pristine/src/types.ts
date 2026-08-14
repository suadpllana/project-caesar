export interface QueryResult {
  query: string;
  items: string[];
  total: number;
}

export type QueryStatus = "idle" | "loading" | "success" | "error";

export interface QueryState {
  query: string;
  status: QueryStatus;
  result: QueryResult | null;
  provisional: boolean;
  error: string | null;
}

export type Transport = (
  query: string,
  signal: AbortSignal,
) => Promise<QueryResult>;

export type Subscriber = (state: QueryState) => void;

export interface Controller {
  search(query: string): void;
  getState(): QueryState;
  subscribe(fn: Subscriber): () => void;
  dispose(): void;
}
