import { describe, expect, it } from "vitest";
import { WORD_PLACEHOLDER_ID, wordStaticParams } from "./routes";

describe("wordStaticParams", () => {
  it("returns one param per word id", () => {
    expect(wordStaticParams([{ id: "你好" }, { id: "谢谢" }])).toEqual([{ id: "你好" }, { id: "谢谢" }]);
  });

  it("returns a placeholder param when no word is visible (Cache Components rejects [])", () => {
    expect(wordStaticParams([])).toEqual([{ id: WORD_PLACEHOLDER_ID }]);
  });
});
