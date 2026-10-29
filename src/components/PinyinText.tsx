import type { Syllable } from "@/lib/dictionary/schema";
import { toneColor, type Tone } from "@/lib/pinyin";

type Props = { syllables: Syllable[]; className?: string };

/** Pinyin with each syllable colored by its tone (Pleco style). */
export function PinyinText({ syllables, className }: Props) {
  return (
    <span className={className}>
      {syllables.map((s, i) => (
        <span key={i} data-tone={s.tone} style={{ color: toneColor(s.tone as Tone) }}>
          {i > 0 ? " " : ""}
          {s.pinyin}
        </span>
      ))}
    </span>
  );
}
