import { createController } from "./controller";
import { createTransport } from "./transport";
import type { Controller, QueryState } from "./types";

interface Harness {
  transport: ReturnType<typeof createTransport>;
  controller: Controller;
  emissions: QueryState[];
  reset(): void;
  addListener(name: string): void;
  removeListener(name: string): void;
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
