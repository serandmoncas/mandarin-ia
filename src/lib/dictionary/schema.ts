import { z } from "zod";

// Mirrors the dictionary.json contract written by the Python pipeline.
// Objects are strict so contract drift (extra/misspelled keys) fails the parse.

export const STATUSES = ["generated", "auto_checked", "human_reviewed"] as const;
export const MISSION_IDS = [
  "introductions",
  "restaurant",
  "transport",
  "hotel",
  "shopping",
  "directions",
  "emergencies",
] as const;

const StatusSchema = z.enum(STATUSES);
const MissionIdSchema = z.enum(MISSION_IDS);
const ToneSchema = z.number().int().min(1).max(5);

const SyllableSchema = z
  .object({ hanzi: z.string(), pinyin: z.string(), tone: ToneSchema })
  .strict();

const AudioRefSchema = z.object({ voice: z.string(), path: z.string() }).strict();

const ExampleSchema = z
  .object({
    zh: z.string(),
    pinyin: z.string(),
    syllables: z.array(SyllableSchema),
    es: z.string(),
    knownBeforeRatio: z.number(),
    audio: AudioRefSchema.nullable(),
  })
  .strict();

const WordEntrySchema = z
  .object({
    id: z.string(),
    simplified: z.string(),
    traditional: z.string(),
    pinyin: z.string(),
    pinyinNumbered: z.string(),
    syllables: z.array(SyllableSchema),
    meaningsEs: z.array(z.string()).min(1).max(4),
    hskLevel: z.number().int().min(1).max(9).nullable(),
    freqRank: z.number().int(),
    order: z.number().int(),
    audio: z.array(AudioRefSchema),
    examples: z.array(ExampleSchema),
    status: StatusSchema,
    flags: z.array(z.string()),
  })
  .strict();

const CharacterInfoSchema = z
  .object({
    char: z.string(),
    components: z.array(z.object({ char: z.string(), meaningEs: z.string() }).strict()),
    mnemonicEs: z.string(),
    status: StatusSchema,
    flags: z.array(z.string()),
  })
  .strict();

const PhraseEntrySchema = z
  .object({
    id: z.string(),
    mission: MissionIdSchema,
    zh: z.string(),
    pinyin: z.string(),
    syllables: z.array(SyllableSchema),
    es: z.string(),
    audio: AudioRefSchema.nullable(),
    status: StatusSchema,
    flags: z.array(z.string()),
  })
  .strict();

export const DictionarySchema = z
  .object({
    version: z.string(),
    generatedAt: z.string(),
    words: z.array(WordEntrySchema),
    characters: z.record(z.string(), CharacterInfoSchema),
    phrases: z.array(PhraseEntrySchema),
    credits: z.array(z.object({ name: z.string(), license: z.string(), url: z.string() }).strict()),
  })
  .strict();

export type Status = z.infer<typeof StatusSchema>;
export type Dictionary = z.infer<typeof DictionarySchema>;
export type WordEntry = z.infer<typeof WordEntrySchema>;
export type PhraseEntry = z.infer<typeof PhraseEntrySchema>;
export type CharacterInfo = z.infer<typeof CharacterInfoSchema>;

/** Only checked content is shown or indexed by the app. */
export function isVisible(e: { status: Status }): boolean {
  return e.status === "auto_checked" || e.status === "human_reviewed";
}
