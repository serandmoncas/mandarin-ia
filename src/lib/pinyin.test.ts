import { describe, expect, it } from "vitest";
import { normalizeForSearch, toneColor } from "./pinyin";

describe("normalizeForSearch", () => {
  it.each([["nihao"], ["ni3hao3"], ["nǐhǎo"], ["ni hao"], ["NIHAO"], ["ni3 hao3"]])(
    "%s → nihao",
    (q) => expect(normalizeForSearch(q)).toBe("nihao"),
  );
  it.each([["lv"], ["lü"], ["lu:"], ["lǜ"], ["lv4"]])("%s → lv", (q) =>
    expect(normalizeForSearch(q)).toBe("lv"),
  );
  it("quita tildes del español", () => expect(normalizeForSearch("Café")).toBe("cafe"));
  it("deja intactos los caracteres han", () => expect(normalizeForSearch("你好")).toBe("你好"));
});

describe("toneColor", () => {
  it("usa los colores estilo Pleco", () => {
    expect(toneColor(1)).toBe("#e53935");
    expect(toneColor(5)).toBe("#9e9e9e");
  });
});
