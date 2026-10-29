// Word ids are Chinese characters, so they must be percent-encoded in URLs.
export function wordHref(id: string): string {
  return `/palabra/${encodeURIComponent(id)}`;
}

export function phraseHref(id: string): string {
  return `/frases#${encodeURIComponent(id)}`;
}
