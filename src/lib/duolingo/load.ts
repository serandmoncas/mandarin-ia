// Server-only (node fs): never import from client components.
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { z } from "zod";

// Mirrors data/duolingo/palabras.json written by scripts/duolingo_build.py.
// The file is personal and git-ignored, so its absence is normal, not an error.

const DuolingoWordSchema = z
  .object({
    hanzi: z.string(),
    pinyin: z.string(),
    meaningsEs: z.array(z.string()).min(1),
    meaningEn: z.string().nullable(),
    section: z.number().int(),
    unit: z.number().int(),
    dictionaryId: z.string().nullable(),
    hskLevel: z.number().int().nullable(),
    freqRank: z.number().int().nullable(),
  })
  .strict();

const DuolingoFileSchema = z
  .object({
    source: z.string(),
    extractedAt: z.string(),
    progress: z.string(),
    words: z.array(DuolingoWordSchema),
    characters: z.array(z.string()),
  })
  .strict();

export type DuolingoWord = z.infer<typeof DuolingoWordSchema>;

export type Duolingo = {
  words: DuolingoWord[];
  /** Dictionary ids of the words already seen in Duolingo. */
  dictionaryIds: Set<string>;
  /** Words seen in Duolingo that the dictionary does not have. */
  extras: DuolingoWord[];
  progress: string | null;
};

const EMPTY: Duolingo = { words: [], dictionaryIds: new Set(), extras: [], progress: null };

/** Resolution order: explicit arg, DUOLINGO_PATH env, then data/duolingo/palabras.json. */
export function resolveDuolingoPath(p?: string): string {
  return p ?? process.env.DUOLINGO_PATH ?? path.join(process.cwd(), "data/duolingo/palabras.json");
}

/** Reads the Duolingo word list; a missing file yields an empty list, a malformed one throws. */
export function loadDuolingo(p?: string): Duolingo {
  const file = resolveDuolingoPath(p);
  if (!existsSync(/*turbopackIgnore: true*/ file)) return EMPTY;
  const d = DuolingoFileSchema.parse(JSON.parse(readFileSync(/*turbopackIgnore: true*/ file, "utf8")));
  return {
    words: d.words,
    dictionaryIds: new Set(d.words.flatMap((w) => (w.dictionaryId ? [w.dictionaryId] : []))),
    extras: d.words.filter((w) => w.dictionaryId === null),
    progress: d.progress,
  };
}

let cached: Duolingo | undefined;

/** Loads the Duolingo list once per server process. */
export function getDuolingo(): Duolingo {
  cached ??= loadDuolingo();
  return cached;
}
