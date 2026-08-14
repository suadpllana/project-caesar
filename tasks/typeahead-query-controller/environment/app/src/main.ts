import { createController } from "./controller";
import { createTransport } from "./transport";
import type { Controller, QueryState } from "./types";

/**
 * Browser harness.
 *
 * Exposes the controller and the test transport on `window.__harness` so the
 * conformance suite can drive them directly, and renders a small panel so the
 * behaviour is observable by hand.
 *
 * Do not modify this file.
 */

interface Harness {
  transport: ReturnType<typeof createTransport>;
  controller: Controller;
  /** State snapshots in emission order, since the last reset. */
  emissions: QueryState[];
  /** Rebuild the controller and clear all recorded activity. */
  reset(): void;
  /** Subscribe an extra listener; returns a handle for unsubscribing. */
  addListener(name: string): void;
  removeListener(name: string): void;
  /** Names of listeners that received at least one emission. */
  listenerHits(): Record<string, number>;
}

declare global {
  interface Window {
    __harness: Harness;
  }
}

const transport = createTransport();

let controller: Controller = createController(transport.transport);
let emissions: QueryState[] = [];
let unsubscribeRecorder: () => void = () => {};
const listeners = new Map<string, () => void>();
const hits: Record<string, number> = {};

function attachRecorder(): void {
  unsubscribeRecorder = controller.subscribe((s) => {
    emissions.push(JSON.parse(JSON.stringify(s)) as QueryState);
    render(s);
  });
}

attachRecorder();

function render(s: QueryState): void {
  const status = document.getElementById("status");
  const results = document.getElementById("results");
  if (status) status.textContent = s.status;
  if (results) {
    results.textContent = s.result
      ? `${s.result.query}: ${s.result.items.join(", ")}`
      : "";
  }
}

window.__harness = {
  transport,
  get controller() {
    return controller;
  },
  get emissions() {
    return emissions;
  },
  reset() {
    controller.dispose();
    unsubscribeRecorder();
    listeners.clear();
    for (const k of Object.keys(hits)) delete hits[k];
    transport.reset();
    emissions = [];
    controller = createController(transport.transport);
    attachRecorder();
  },
  addListener(name: string) {
    hits[name] = 0;
    const off = controller.subscribe(() => {
      hits[name] = (hits[name] ?? 0) + 1;
    });
    listeners.set(name, off);
  },
  removeListener(name: string) {
    const off = listeners.get(name);
    if (off) off();
    listeners.delete(name);
  },
  listenerHits: () => ({ ...hits }),
} as Harness;

const input = document.getElementById("q") as HTMLInputElement | null;
if (input) {
  input.addEventListener("input", () => {
    controller.search(input.value);
  });
}
