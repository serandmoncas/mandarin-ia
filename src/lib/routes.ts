// Word ids are Chinese characters, so they must be percent-encoded in URLs.
export function wordHref(id: string): string {
  return `/palabra/${encodeURIComponent(id)}`;
}

export function phraseHref(id: string): string {
  return `/frases#${encodeURIComponent(id)}`;
}

/**
 * Never a real word id: it only exists so the build can validate /palabra/[id] when no
 * word is visible yet; the page answers it with notFound().
 */
export const WORD_PLACEHOLDER_ID = "__sin-palabras__";

/**
 * Static params for /palabra/[id]. With Cache Components an empty list is a build error,
 * so a dictionary with zero visible words yields a single placeholder param
 * (the approach recommended in Next's generateStaticParams docs).
 */
export function wordStaticParams(words: { id: string }[]): { id: string }[] {
  return words.length > 0 ? words.map((w) => ({ id: w.id })) : [{ id: WORD_PLACEHOLDER_ID }];
}
