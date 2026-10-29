// Server-only: memoized access to the visible dictionary for pages.
import { loadDictionary } from "./load";
import type { Dictionary } from "./schema";

let cached: Dictionary | undefined;

/** Loads the dictionary once per server process and sorts words by learning order. */
export function getDictionary(): Dictionary {
  if (!cached) {
    const d = loadDictionary();
    cached = { ...d, words: [...d.words].sort((a, b) => a.order - b.order) };
  }
  return cached;
}

