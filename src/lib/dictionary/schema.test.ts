import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { DictionarySchema, isVisible } from "./schema";
import { loadDictionary } from "./load";
import { buildSearchIndex } from "../search";

const SAMPLE = path.join(process.cwd(), "data/fixtures/dictionary.sample.json");

describe("DictionarySchema", () => {
  it("parses the Python fixture", () => {
    const json = JSON.parse(readFileSync(SAMPLE, "utf8"));
    expect(() => DictionarySchema.parse(json)).not.toThrow();
  });

  it("rejects unexpected keys (contract drift)", () => {
    const json = JSON.parse(readFileSync(SAMPLE, "utf8"));
    json.words[0].pinyinNumberd = "x";
    expect(() => DictionarySchema.parse(json)).toThrow();
  });

  it("rejects an out-of-range tone", () => {
    const json = JSON.parse(readFileSync(SAMPLE, "utf8"));
    json.words[0].syllables[0].tone = 6;
    expect(() => DictionarySchema.parse(json)).toThrow();
  });

  it("isVisible only accepts checked statuses", () => {
    expect(isVisible({ status: "generated" })).toBe(false);
    expect(isVisible({ status: "auto_checked" })).toBe(true);
    expect(isVisible({ status: "human_reviewed" })).toBe(true);
  });
});

describe("loadDictionary", () => {
  it("hides non-visible words, phrases and characters", () => {
    const d = loadDictionary(SAMPLE);
    expect(d.words.map((w) => w.id)).not.toContain("你");
    expect(d.words.map((w) => w.id)).toContain("你好");
    expect(d.phrases.map((p) => p.id)).not.toContain("phrase:restaurant:000");
    expect(d.phrases.map((p) => p.id)).toContain("phrase:introductions:000");
    expect(Object.values(d.characters).every(isVisible)).toBe(true);
  });

  it("fails with a helpful message when the file is missing", () => {
    expect(() => loadDictionary("/nonexistent/dictionary.json")).toThrow(
      /DICTIONARY_PATH=data\/fixtures\/dictionary\.sample\.json/,
    );
  });

  it("search index excludes hidden entries", () => {
    const ids = buildSearchIndex(loadDictionary(SAMPLE)).map((d) => d.id);
    expect(ids).not.toContain("你");
    expect(ids).not.toContain("phrase:restaurant:000");
    expect(ids).toContain("你好");
  });
});
