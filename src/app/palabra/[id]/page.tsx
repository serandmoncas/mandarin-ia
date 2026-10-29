import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { AudioButton } from "@/components/AudioButton";
import { PinyinText } from "@/components/PinyinText";
import { getDictionary } from "@/lib/dictionary/get";
import type { CharacterInfo, WordEntry } from "@/lib/dictionary/schema";

// Every visible word is prerendered via generateStaticParams, so only unknown ids reach a
// request-time render. Those must block (not stream) so notFound() yields a real 404 status.
export const instant = false;

export function generateStaticParams() {
  return getDictionary().words.map((w) => ({ id: w.id }));
}

/** Route params may arrive percent-encoded (non-ASCII ids); decode defensively. */
function decodeId(raw: string): string {
  try {
    return decodeURIComponent(raw);
  } catch {
    return raw;
  }
}

function findWord(raw: string): WordEntry | undefined {
  const id = decodeId(raw);
  return getDictionary().words.find((w) => w.id === id);
}

export async function generateMetadata({ params }: PageProps<"/palabra/[id]">): Promise<Metadata> {
  const word = findWord((await params).id);
  return word ? { title: `${word.simplified} (${word.pinyin})`, description: word.meaningsEs.join("; ") } : {};
}

function reportHref(id: string): string {
  return `mailto:?subject=${encodeURIComponent(`Error en mandarin-ia: ${id}`)}`;
}

export default async function WordPage({ params }: PageProps<"/palabra/[id]">) {
  const word = findWord((await params).id);
  if (!word) notFound();

  const { characters } = getDictionary();
  const chars = [...new Set(Array.from(word.simplified))]
    .map((c) => characters[c])
    .filter((c): c is CharacterInfo => c !== undefined);

  return (
    <article className="flex flex-col gap-8">
      <header className="flex flex-col items-center gap-3 pt-4 text-center">
        <h1 lang="zh-CN" className="font-hanzi text-7xl leading-tight">
          {word.simplified}
        </h1>
        {word.traditional !== word.simplified && (
          <p className="text-sm text-subtle">
            Tradicional: <span lang="zh-TW" className="font-hanzi">{word.traditional}</span>
          </p>
        )}
        <PinyinText syllables={word.syllables} className="text-2xl font-medium" />
        <div className="flex flex-wrap justify-center gap-2">
          {word.audio.map((a, i) => (
            <AudioButton key={a.path} audio={a} label={`Voz ${i + 1}`} />
          ))}
        </div>
      </header>

      <section className="flex flex-col gap-3" aria-labelledby="meanings">
        <h2 id="meanings" className="text-lg font-semibold">
          Significados
        </h2>
        <ol className="list-decimal space-y-1 pl-6 text-lg">
          {word.meaningsEs.map((m) => (
            <li key={m}>{m}</li>
          ))}
        </ol>
        <p className="flex gap-2 text-sm text-subtle">
          {word.hskLevel !== null && <span className="rounded-full bg-muted px-2 py-1">HSK {word.hskLevel}</span>}
          <span className="rounded-full bg-muted px-2 py-1">#{word.freqRank} en frecuencia</span>
        </p>
      </section>

      {word.examples.length > 0 && (
        <section className="flex flex-col gap-3" aria-labelledby="examples">
          <h2 id="examples" className="text-lg font-semibold">
            Ejemplos
          </h2>
          <ul className="flex flex-col gap-3">
            {word.examples.map((ex) => (
              <li key={ex.zh} className="flex flex-col gap-1 rounded-2xl border border-line bg-surface p-4">
                <p lang="zh-CN" className="font-hanzi text-2xl">
                  {ex.zh}
                </p>
                <PinyinText syllables={ex.syllables} />
                <p className="text-subtle">{ex.es}</p>
                <div className="pt-1">
                  <AudioButton audio={ex.audio} label="Escuchar" />
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      {chars.length > 0 && (
        <section className="flex flex-col gap-3" aria-labelledby="characters">
          <h2 id="characters" className="text-lg font-semibold">
            Caracteres
          </h2>
          <ul className="flex flex-col gap-3">
            {chars.map((c) => (
              <li key={c.char} className="flex gap-4 rounded-2xl border border-line bg-surface p-4">
                <span lang="zh-CN" className="font-hanzi text-5xl leading-none">
                  {c.char}
                </span>
                <div className="flex flex-col gap-1">
                  {c.components.length > 0 && (
                    <p className="text-sm">
                      {c.components.map((p, i) => (
                        <span key={`${p.char}-${i}`}>
                          {i > 0 && " + "}
                          <span lang="zh-CN" className="font-hanzi">
                            {p.char}
                          </span>{" "}
                          <span className="text-subtle">({p.meaningEs})</span>
                        </span>
                      ))}
                    </p>
                  )}
                  <p>{c.mnemonicEs}</p>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      <footer className="border-t border-line pt-4">
        <a href={reportHref(word.id)} className="inline-flex min-h-11 items-center text-sm text-subtle underline">
          Reportar error
        </a>
      </footer>
    </article>
  );
}
