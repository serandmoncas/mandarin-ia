import Link from "next/link";
import { Suspense } from "react";
import { SearchBox } from "@/components/SearchBox";
import { WordCard } from "@/components/WordCard";
import { getDictionary } from "@/lib/dictionary/get";

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

/** Parses ?p= (1-based); invalid values fall back to 1 and out-of-range values are clamped. */
function pageFromParam(raw: string | string[] | undefined, totalPages: number): number {
  const n = Number.parseInt(Array.isArray(raw) ? (raw[0] ?? "") : (raw ?? ""), 10);
  if (!Number.isFinite(n) || n < 1) return 1;
  return Math.min(n, totalPages);
}

async function WordList({ searchParams }: Pick<PageProps<"/">, "searchParams">) {
  const { words } = getDictionary();
  const totalPages = Math.max(1, Math.ceil(words.length / PAGE_SIZE));
  const page = pageFromParam((await searchParams).p, totalPages);
  const slice = words.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  if (words.length === 0) return <p className="text-sm text-subtle">Todavía no hay palabras.</p>;

  return (
    <>
      <ol className="flex flex-col gap-2" start={(page - 1) * PAGE_SIZE + 1}>
        {slice.map((w) => (
          <li key={w.id}>
            <WordCard word={w} />
          </li>
        ))}
      </ol>
      {totalPages > 1 && (
        <nav className="flex items-center justify-between gap-2 pt-2" aria-label="Paginación">
          {page > 1 ? (
            <Link href={`/?p=${page - 1}`} className="flex min-h-11 items-center rounded-xl border border-line bg-surface px-4">
              ← Anterior
            </Link>
          ) : (
            <span />
          )}
          <span className="text-sm text-subtle">
            Página {page} de {totalPages}
          </span>
          {page < totalPages ? (
            <Link href={`/?p=${page + 1}`} className="flex min-h-11 items-center rounded-xl border border-line bg-surface px-4">
              Siguiente →
            </Link>
          ) : (
            <span />
          )}
        </nav>
      )}
    </>
  );
}
