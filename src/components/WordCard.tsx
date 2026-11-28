import Link from "next/link";
import { wordHref } from "@/lib/routes";
import type { WordEntry } from "@/lib/dictionary/schema";
import { PinyinText } from "./PinyinText";

/** Compact list item: hanzi, colored pinyin, first meaning, HSK level and Duolingo mark. */
export function WordCard({ word, seenInDuolingo = false }: { word: WordEntry; seenInDuolingo?: boolean }) {
  return (
    <Link
      href={wordHref(word.id)}
      className="flex min-h-16 items-center gap-4 rounded-2xl border border-line bg-surface px-4 py-3 active:bg-muted"
    >
      <span lang="zh-CN" className="font-hanzi text-3xl leading-none">
        {word.simplified}
      </span>
      <span className="flex min-w-0 flex-1 flex-col">
        <PinyinText syllables={word.syllables} className="text-base font-medium" />
        <span className="truncate text-sm text-subtle">{word.meaningsEs[0]}</span>
      </span>
      {seenInDuolingo && (
        <span
          title="Ya la viste en Duolingo"
          className="shrink-0 rounded-full border border-line px-2 py-1 text-xs font-semibold"
        >
          Duolingo
        </span>
      )}
      {word.hskLevel !== null && (
        <span className="shrink-0 rounded-full bg-muted px-2 py-1 text-xs font-semibold text-subtle">
          HSK {word.hskLevel}
        </span>
      )}
    </Link>
  );
}
