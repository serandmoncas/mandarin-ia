import type { Metadata } from "next";
import { getDictionary } from "@/lib/dictionary/get";

export const metadata: Metadata = { title: "Créditos" };

export default function CreditsPage() {
  const { credits } = getDictionary();
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold">Créditos</h1>
      <p className="text-subtle">Esta app se construye con datos y servicios de terceros:</p>
      <ul className="flex flex-col gap-3">
        {credits.map((c) => (
          <li key={c.name} className="flex flex-col gap-1 rounded-2xl border border-line bg-surface p-4">
            <a href={c.url} target="_blank" rel="noopener noreferrer" className="font-semibold underline">
              {c.name}
            </a>
            <span className="text-sm text-subtle">Licencia: {c.license}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
