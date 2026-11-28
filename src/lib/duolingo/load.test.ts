import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { loadDuolingo } from "./load";

const sample = {
  source: "Duolingo",
  extractedAt: "2026-11-28",
  progress: "Sección 1, unidad 7",
  words: [
    {
      hanzi: "水", pinyin: "shuǐ", meaningsEs: ["agua"], meaningEn: "water",
      section: 1, unit: 1, dictionaryId: "水", hskLevel: 1, freqRank: 200,
    },
    {
      hanzi: "粥", pinyin: "zhōu", meaningsEs: ["gachas de arroz"], meaningEn: null,
      section: 1, unit: 1, dictionaryId: null, hskLevel: null, freqRank: null,
    },
  ],
  characters: ["水", "粥"],
};

function writeTemp(content: string): string {
  const file = path.join(mkdtempSync(path.join(tmpdir(), "duo-")), "palabras.json");
  writeFileSync(file, content);
  return file;
}

describe("loadDuolingo", () => {
  it("returns an empty list when the file does not exist", () => {
    const d = loadDuolingo("/no/existe/palabras.json");
    expect(d.words).toEqual([]);
    expect(d.dictionaryIds.size).toBe(0);
  });

  it("indexes the words that exist in the dictionary", () => {
    const d = loadDuolingo(writeTemp(JSON.stringify(sample)));
    expect(d.words).toHaveLength(2);
    expect([...d.dictionaryIds]).toEqual(["水"]);
  });

  it("separates words missing from the dictionary", () => {
    const d = loadDuolingo(writeTemp(JSON.stringify(sample)));
    expect(d.extras.map((w) => w.hanzi)).toEqual(["粥"]);
  });

  it("rejects a malformed file instead of hiding the error", () => {
    expect(() => loadDuolingo(writeTemp(JSON.stringify({ words: [{ hanzi: 1 }] })))).toThrow();
  });
});
