export type Tone = 1 | 2 | 3 | 4 | 5;

// Pleco-style tone colors (5 = neutral tone).
const TONE_COLORS: Record<Tone, string> = {
  1: "#e53935",
  2: "#fb8c00",
  3: "#43a047",
  4: "#1e88e5",
  5: "#9e9e9e",
};

export function toneColor(tone: Tone): string {
  return TONE_COLORS[tone];
}

/**
 * Normalizes a search query so that pinyin typed with tone marks, tone numbers,
 * "u:" / "ü" / "v", spaces or apostrophes all match the same indexed form.
 * Han characters are left untouched.
 */
export function normalizeForSearch(s: string): string {
  return s
    .toLowerCase()
    .normalize("NFD") // ü / ǜ decompose to "u" + U+0308 (+ tone mark)
    .replace(/u\u0308|u:|v/g, "v") // must run before stripping diacritics
    .replace(/\p{M}/gu, "")
    .replace(/[1-5\s'’-]/g, "");
}
