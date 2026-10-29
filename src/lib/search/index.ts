import type { Dictionary } from "../dictionary/schema";
import { isVisible } from "../dictionary/visibility";
import { normalizeForSearch } from "../pinyin";

export type SearchDoc = {
  id: string;
  kind: "word" | "phrase";
  hanzi: string;
  pinyinKey: string;
  esKeys: string[];
  order: number;
};

/** Normalized full text plus each individual normalized word, deduplicated. */
function spanishKeys(texts: string[]): string[] {
  const keys = new Set<string>();
  for (const t of texts) {
    keys.add(normalizeForSearch(t));
    for (const w of t.split(/[\s.,;:!?¿¡()"]+/)) keys.add(normalizeForSearch(w));
  }
  keys.delete("");
  return [...keys];
}

// Phrases have no learning order; words rank ahead of them on ties.
const PHRASE_ORDER = Number.MAX_SAFE_INTEGER;

export function buildSearchIndex(d: Dictionary): SearchDoc[] {
  const words: SearchDoc[] = d.words
    .filter(isVisible)
    .map((w) => ({
      id: w.id,
      kind: "word",
      hanzi: w.simplified,
      pinyinKey: normalizeForSearch(w.pinyinNumbered),
      esKeys: spanishKeys(w.meaningsEs),
      order: w.order,
    }));
  const phrases: SearchDoc[] = d.phrases
    .filter(isVisible)
    .map((p) => ({
      id: p.id,
      kind: "phrase",
      hanzi: p.zh,
      pinyinKey: normalizeForSearch(p.pinyin),
      esKeys: spanishKeys([p.es]),
      order: PHRASE_ORDER,
    }));
  return [...words, ...phrases];
}

// TODO(Sergio): replace this baseline ranking (returns 0 = no match). Trade-offs:
//  - exact hanzi vs. hanzi substring vs. pinyin prefix vs. Spanish word: which wins
//    when a query like "ma" matches all of them?
//  - should a whole Spanish word ("madre") outrank a pinyin prefix?
//  - ties are broken by `order` (lower = learned earlier) in searchEntries.
function scoreMatch(doc: SearchDoc, q: string): number {
  if (doc.hanzi.includes(q)) return doc.hanzi === q ? 100 : 80;
  if (doc.pinyinKey.startsWith(q)) return 60;
  if (doc.esKeys.some((k) => k === q)) return 50;
  if (doc.esKeys.some((k) => k.startsWith(q))) return 40;
  if (doc.pinyinKey.includes(q)) return 30;
  if (doc.esKeys.some((k) => k.includes(q))) return 20;
  return 0;
}

export function searchEntries(index: SearchDoc[], query: string, limit = 20): SearchDoc[] {
  const q = normalizeForSearch(query.trim());
  if (!q) return [];
  return index
    .map((doc) => ({ doc, score: scoreMatch(doc, q) }))
    .filter((m) => m.score > 0)
    .sort((a, b) => b.score - a.score || a.doc.order - b.doc.order)
    .slice(0, limit)
    .map((m) => m.doc);
}
