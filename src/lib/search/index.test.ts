import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { DictionarySchema, type Dictionary, type WordEntry } from "../dictionary/schema";
import { buildSearchIndex, searchEntries } from "./index";

const sample = DictionarySchema.parse(
  JSON.parse(readFileSync(path.join(process.cwd(), "data/fixtures/dictionary.sample.json"), "utf8")),
);
// Only visible entries, mimicking loadDictionary.
const visible: Dictionary = {
  ...sample,
  words: sample.words.filter((w) => w.status !== "generated"),
  phrases: sample.phrases.filter((p) => p.status !== "generated"),
};
const index = buildSearchIndex(visible);

function word(over: Partial<WordEntry> & { id: string }): WordEntry {
  return {
    ...sample.words[0],
    simplified: over.id,
    traditional: over.id,
    ...over,
  };
}

describe("searchEntries", () => {
  it.each(["nihao", "ni3hao3", "nǐhǎo", "ni hao"])("finds 你好 first for %s", (q) => {
    expect(searchEntries(index, q)[0]?.id).toBe("你好");
  });

  it("finds by Spanish word", () => {
    expect(searchEntries(index, "hola").map((d) => d.id)).toContain("phrase:introductions:000");
    expect(searchEntries(index, "saludo")[0]?.id).toBe("你好");
  });

  it("finds by hanzi", () => {
    expect(searchEntries(index, "你")[0]?.id).toBe("你好");
  });

  it("returns [] for empty or blank query", () => {
    expect(searchEntries(index, "")).toEqual([]);
    expect(searchEntries(index, "   ")).toEqual([]);
  });

  it("matches accent-insensitively: cafe finds café", () => {
    const d: Dictionary = {
      ...sample,
      phrases: [],
      words: [
        word({ id: "水", pinyinNumbered: "shui3", meaningsEs: ["agua"], order: 1 }),
        word({ id: "咖啡", pinyinNumbered: "ka1 fei1", meaningsEs: ["café"], order: 2 }),
      ],
    };
    expect(searchEntries(buildSearchIndex(d), "cafe").map((x) => x.id)).toEqual(["咖啡"]);
  });

  it("breaks ties by lower order", () => {
    const d: Dictionary = {
      ...sample,
      phrases: [],
      words: [
        word({ id: "甲", pinyinNumbered: "ma1", meaningsEs: ["madre"], order: 9 }),
        word({ id: "乙", pinyinNumbered: "ma2", meaningsEs: ["madre"], order: 2 }),
      ],
    };
    expect(searchEntries(buildSearchIndex(d), "madre").map((x) => x.id)).toEqual(["乙", "甲"]);
  });

  it("respects limit", () => {
    expect(searchEntries(index, "n", 1).length).toBeLessThanOrEqual(1);
  });
});
