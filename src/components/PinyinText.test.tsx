import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PinyinText } from "./PinyinText";

describe("PinyinText", () => {
  it("PinyinText colors each syllable", () => {
    const { container } = render(
      <PinyinText
        syllables={[
          { hanzi: "你", pinyin: "nǐ", tone: 3 },
          { hanzi: "好", pinyin: "hǎo", tone: 3 },
        ]}
      />,
    );
    const spans = container.querySelectorAll("span[data-tone]");
    expect(spans).toHaveLength(2);
    expect(spans[0]).toHaveTextContent("nǐ");
    expect(spans[1]).toHaveTextContent("hǎo");
    for (const s of spans) expect(s).toHaveStyle({ color: "#43a047" });
  });

  it("uses the neutral color for tone 5", () => {
    const { container } = render(<PinyinText syllables={[{ hanzi: "吗", pinyin: "ma", tone: 5 }]} />);
    expect(container.querySelector("span[data-tone]")).toHaveStyle({ color: "#9e9e9e" });
  });
});
