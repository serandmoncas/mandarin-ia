import Link from "next/link";
import { Suspense } from "react";
import { SearchBox } from "@/components/SearchBox";
import { WordCard } from "@/components/WordCard";
import { getDictionary } from "@/lib/dictionary/get";
import { getDuolingo, type DuolingoWord } from "@/lib/duolingo/load";

const PAGE_SIZE = 50;

export default function Home({ searchParams }: PageProps<"/">) {
  return (
    <div className="flex flex-col gap-8">
      <SearchBox />
      <section className="flex flex-col gap-3" aria-labelledby="order-title">
        <h1 id="order-title" className="text-lg font-semibold">
          Por orden de aprendizaje
        </h1>
        <Suspense fallback={<p className="text-sm text-subtle">Cargando…</p>}>
          <WordList searchParams={searchParams} />
        </Suspense>
      </section>
    </div>
  );
}

function firstParam(raw: string | string[] | undefined): string {
  return Array.isArray(raw) ? (raw[0] ?? "") : (raw ?? "");
}

/** Parses ?p= (1-based); invalid values fall back to 1 and out-of-range values are clamped. */
function pageFromParam(raw: string | string[] | undefined, totalPages: number): number {
  const n = Number.parseInt(firstParam(raw), 10);
  if (!Number.isFinite(n) || n < 1) return 1;
  return Math.min(n, totalPages);
}

function listHref(page: number, onlyDuolingo: boolean): string {
  const params = new URLSearchParams();
  if (onlyDuolingo) params.set("duolingo", "1");
  if (page > 1) params.set("p", String(page));
  const qs = params.toString();
  return qs ? `/?${qs}` : "/";
}

async function WordList({ searchParams }: Pick<PageProps<"/">, "searchParams">) {
  const sp = await searchParams;
  const duolingo = getDuolingo();
  const onlyDuolingo = firstParam(sp.duolingo) === "1" && duolingo.words.length > 0;

  const all = getDictionary().words;
  const words = onlyDuolingo ? all.filter((w) => duolingo.dictionaryIds.has(w.id)) : all;
  const totalPages = Math.max(1, Math.ceil(words.length / PAGE_SIZE));
  const page = pageFromParam(sp.p, totalPages);
  const slice = words.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const pill = "flex min-h-11 items-center rounded-xl border border-line bg-surface px-4";

  return (
    <>
      {duolingo.words.length > 0 && (
        <nav className="flex flex-wrap gap-2" aria-label="Filtro">
          <Link href={listHref(1, false)} aria-current={!onlyDuolingo ? "page" : undefined}
            className={`${pill} text-sm ${!onlyDuolingo ? "font-semibold" : "text-subtle"}`}>
            Todas
          </Link>
          <Link href={listHref(1, true)} aria-current={onlyDuolingo ? "page" : undefined}
            className={`${pill} text-sm ${onlyDuolingo ? "font-semibold" : "text-subtle"}`}>
            Mis palabras de Duolingo ({duolingo.dictionaryIds.size})
          </Link>
        </nav>
      )}

      {words.length === 0 ? (
        <p className="text-sm text-subtle">Todavía no hay palabras.</p>
      ) : (
        <ol className="flex flex-col gap-2" start={(page - 1) * PAGE_SIZE + 1}>
          {slice.map((w) => (
            <li key={w.id}>
              <WordCard word={w} seenInDuolingo={duolingo.dictionaryIds.has(w.id)} />
            </li>
          ))}
        </ol>
      )}

      {totalPages > 1 && (
        <nav className="flex items-center justify-between gap-2 pt-2" aria-label="Paginación">
          {page > 1 ? <Link href={listHref(page - 1, onlyDuolingo)} className={pill}>← Anterior</Link> : <span />}
          <span className="text-sm text-subtle">
            Página {page} de {totalPages}
          </span>
          {page < totalPages ? <Link href={listHref(page + 1, onlyDuolingo)} className={pill}>Siguiente →</Link> : <span />}
        </nav>
      )}

      {onlyDuolingo && duolingo.extras.length > 0 && <DuolingoExtras words={duolingo.extras} />}
    </>
  );
}

/** Words seen in Duolingo that the dictionary lacks: shown plainly, without a detail page. */
function DuolingoExtras({ words }: { words: DuolingoWord[] }) {
  return (
    <section className="flex flex-col gap-2 pt-4" aria-labelledby="extras-title">
      <h2 id="extras-title" className="text-base font-semibold">
        También en Duolingo, fuera del diccionario
      </h2>
      <p className="text-sm text-subtle">Combinaciones y palabras que no están entre las 2500 más frecuentes.</p>
      <ul className="flex flex-col gap-2">
        {words.map((w) => (
          <li key={w.hanzi} className="flex min-h-16 items-center gap-4 rounded-2xl border border-line bg-surface px-4 py-3">
            <span lang="zh-CN" className="font-hanzi text-3xl leading-none">
              {w.hanzi}
            </span>
            <span className="flex min-w-0 flex-1 flex-col">
              <span className="text-base font-medium">{w.pinyin}</span>
              <span className="truncate text-sm text-subtle">{w.meaningsEs[0]}</span>
            </span>
            <span className="shrink-0 text-xs text-subtle">Unidad {w.unit}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
