"use client";

import Link from "next/link";
import { useMemo, useRef, useState } from "react";
import { phraseHref, wordHref } from "@/lib/routes";
import { searchEntries, type SearchDoc } from "@/lib/search";

type IndexState = { status: "idle" | "loading" | "error" } | { status: "ready"; docs: SearchDoc[] };

function hrefFor(doc: SearchDoc): string {
  return doc.kind === "word" ? wordHref(doc.id) : phraseHref(doc.id);
}

/** Client-side search over /search-index.json, fetched once on first use. */
export function SearchBox() {
  const [query, setQuery] = useState("");
  const [index, setIndex] = useState<IndexState>({ status: "idle" });
  const requested = useRef(false);

  function ensureIndex() {
    if (requested.current) return;
    requested.current = true;
    setIndex({ status: "loading" });
    fetch("/search-index.json")
      .then((r) => {
        if (!r.ok) throw new Error(String(r.status));
        return r.json() as Promise<SearchDoc[]>;
      })
      .then((docs) => setIndex({ status: "ready", docs }))
      .catch(() => {
        requested.current = false;
        setIndex({ status: "error" });
      });
  }

  const results = useMemo(
    () => (index.status === "ready" ? searchEntries(index.docs, query) : []),
    [index, query],
  );
  const hasQuery = query.trim() !== "";

  return (
    <div className="flex flex-col gap-3">
      <label htmlFor="search" className="sr-only">
        Buscar
      </label>
      <input
        id="search"
        type="search"
        inputMode="search"
        autoComplete="off"
        autoCapitalize="none"
        spellCheck={false}
        placeholder="Busca en caracteres, pinyin o español"
        value={query}
        onFocus={ensureIndex}
        onChange={(e) => {
          ensureIndex();
          setQuery(e.target.value);
        }}
        className="min-h-12 w-full rounded-2xl border border-line bg-surface px-4 text-base outline-none focus:border-accent"
      />
      <p role="status" aria-live="polite" className="text-sm text-subtle empty:sr-only">
        {hasQuery && index.status === "loading" && "Cargando…"}
        {hasQuery && index.status === "error" && "No se pudo cargar el índice de búsqueda."}
        {hasQuery && index.status === "ready" && results.length === 0 && "Sin resultados."}
      </p>
      {results.length > 0 && (
        <ul className="flex flex-col gap-2" aria-label="Resultados">
          {results.map((doc) => (
            <li key={`${doc.kind}:${doc.id}`}>
              <Link
                href={hrefFor(doc)}
                className="flex min-h-12 items-center gap-3 rounded-xl border border-line bg-surface px-4 py-2 active:bg-muted"
              >
                <span lang="zh-CN" className="font-hanzi shrink-0 text-2xl">
                  {doc.hanzi}
                </span>
                <span className="flex min-w-0 flex-1 flex-col">
                  <span className="truncate text-sm font-medium">{doc.pinyin}</span>
                  <span className="truncate text-sm text-subtle">{doc.gloss}</span>
                </span>
                <span className="shrink-0 text-xs text-subtle">{doc.kind === "word" ? "Palabra" : "Frase"}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
