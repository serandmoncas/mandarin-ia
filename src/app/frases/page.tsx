import type { Metadata } from "next";
import { AudioButton } from "@/components/AudioButton";
import { PinyinText } from "@/components/PinyinText";
import { getDictionary } from "@/lib/dictionary/get";
import { MISSION_IDS } from "@/lib/dictionary/schema";
import { MISSION_LABELS } from "@/lib/missions";

export const metadata: Metadata = { title: "Frases de viaje" };

export default function PhrasesPage() {
  const { phrases } = getDictionary();
  const groups = MISSION_IDS.map((m) => ({ mission: m, items: phrases.filter((p) => p.mission === m) })).filter(
    (g) => g.items.length > 0,
  );

  return (
    <div className="flex flex-col gap-8">
      <h1 className="text-2xl font-bold">Frases de viaje</h1>
      {groups.length === 0 && <p className="text-subtle">Todavía no hay frases.</p>}
      {groups.map((g) => (
        <section key={g.mission} className="flex flex-col gap-3" aria-labelledby={`mission-${g.mission}`}>
          <h2 id={`mission-${g.mission}`} className="text-lg font-semibold">
            {MISSION_LABELS[g.mission]}
          </h2>
          <ul className="flex flex-col gap-3">
            {g.items.map((p) => (
              <li key={p.id} id={p.id} className="flex scroll-mt-20 flex-col gap-1 rounded-2xl border border-line bg-surface p-4 target:border-accent target:ring-2 target:ring-accent">
                <p lang="zh-CN" className="font-hanzi text-2xl">
                  {p.zh}
                </p>
                <PinyinText syllables={p.syllables} />
                <p className="text-subtle">{p.es}</p>
                <div className="pt-1">
                  <AudioButton audio={p.audio} label="Escuchar" ariaLabel={`Escuchar frase: ${p.zh}`} />
                </div>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
