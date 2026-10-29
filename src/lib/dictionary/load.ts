// Server-only (node fs): never import from client components.
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { DictionarySchema, isVisible, type Dictionary } from "./schema";

/** Resolution order: explicit arg, DICTIONARY_PATH env, then data/dictionary.json. */
export function resolveDictionaryPath(p?: string): string {
  return p ?? process.env.DICTIONARY_PATH ?? path.join(process.cwd(), "data/dictionary.json");
}

/** Reads and validates the dictionary, dropping every non-visible entry. Server-only. */
export function loadDictionary(p?: string): Dictionary {
  const file = resolveDictionaryPath(p);
  if (!existsSync(file)) {
    throw new Error(
      `Dictionary not found at ${file}. For local development use ` +
        `DICTIONARY_PATH=data/fixtures/dictionary.sample.json`,
    );
  }
  const d = DictionarySchema.parse(JSON.parse(readFileSync(file, "utf8")));
  return {
    ...d,
    words: d.words.filter(isVisible),
    phrases: d.phrases.filter(isVisible),
    characters: Object.fromEntries(Object.entries(d.characters).filter(([, c]) => isVisible(c))),
  };
}
