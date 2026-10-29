"use client";

import { useRef, useState } from "react";
import type { AudioRef } from "@/lib/dictionary/schema";

type Props = { audio: AudioRef | null; label: string };

/** Play button for one audio clip. Renders nothing if there is no clip or no audio host. */
export function AudioButton({ audio, label }: Props) {
  const player = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const base = process.env.NEXT_PUBLIC_AUDIO_BASE_URL;
  if (!audio || !base) return null;
  const src = base + audio.path;

  function play() {
    if (!player.current) {
      player.current = new Audio(src);
      player.current.addEventListener("ended", () => setPlaying(false));
      player.current.addEventListener("error", () => setPlaying(false));
    }
    player.current.currentTime = 0;
    setPlaying(true);
    player.current.play().catch(() => setPlaying(false));
  }

  return (
    <button
      type="button"
      onClick={play}
      aria-label={`Escuchar: ${label}`}
      className="inline-flex min-h-11 min-w-11 items-center gap-2 rounded-full border border-line bg-surface px-4 text-sm font-medium active:scale-95"
    >
      <span aria-hidden="true">{playing ? "🔊" : "▶"}</span>
      {label}
    </button>
  );
}
