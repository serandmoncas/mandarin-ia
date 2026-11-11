# Backlog — mandarin-ia

Última actualización: 2026-11-11. Rama de trabajo: `feat/fase-1-diccionario` (sin remoto todavía).
Diseño: `docs/superpowers/specs/2026-10-29-mandarin-ia-design.md` · Plan Fase 1: `docs/superpowers/plans/2026-10-29-fase-1-diccionario.md`.

## Estado de la Fase 1 (Diccionario)

- [x] Tareas 1–7, 9 y 10 del plan: pipeline Python, contrato JSON, app Next.js (PWA), búsqueda, ficha de palabra, frases, créditos. Revisión final de la rama: limpia.
- [x] Tarea 8 (parte texto): generación + revisión automática + build ejecutados (2026-10-29).
  - Palabras: 2500 → 1739 `auto_checked` (70 %), 761 ocultas. **Meta ≥90 % no alcanzada.**
  - Caracteres: 1039 → 976 aprobados. Frases: 202 → 174 aprobadas. Entradas con flag `review`: 962.
- [ ] Tarea 8 (parte audio) y Tarea 11 (despliegue): ver abajo.

## Pendiente (en orden)

1. [ ] **Cuentas** (Sergio, guía en `docs/setup.md`). `.env` ya existe vacío (gitignored, chmod 600).
   - [ ] Supabase: proyecto `mandarin-ia` plan Free + bucket público `audio`; copiar Project URL y `service_role` al `.env`. Quedó detenido en el login con GitHub.
   - [ ] Azure Speech: recurso **F0** (nunca S0), región `eastus`; copiar KEY 1 y región al `.env`.
   - [ ] `NEXT_PUBLIC_AUDIO_BASE_URL={SUPABASE_URL}/storage/v1/object/public/audio/` (con barra final).
2. [ ] Prueba de audio: `audio --limit 5`.
3. [ ] Analizar por qué 962 entradas quedaron con flag `review` (70 % vs. meta 90 %); corregir prompts/checks y regenerar lo necesario.
4. [ ] Revisar 20 palabras al azar con Sergio.
5. [ ] Audio completo: `audio` (~16 h a ≤18 clips/min, reanudable) → `build` → commit con `data/audio-manifest.json`.
6. [ ] Tarea 11: despliegue en Vercel Hobby — **solo con aprobación de Sergio**; requiere `NEXT_PUBLIC_AUDIO_BASE_URL` en build.
7. [ ] Integrar la rama: merge a `main` o PR (crear remoto en GitHub primero).
8. [ ] Opcional (Sergio): reescribir `scoreMatch` en `src/lib/search/index.ts`.

## Fases siguientes (del diseño)

- Fase 2+: sesión diaria de 30 min (5 bloques), tonos con pares mínimos, FSRS, misiones de viaje, tutor en vivo con Gemini free tier, evaluación de pronunciación con Azure. Meta: HSK 3.0 nivel 2 + HSKK básico a inicios de 2028.

## Comandos

```bash
# Pipeline (desde la raíz)
p() { uv run --directory scripts python -m mandarin_pipeline "$@"; }
p stats | p review | p build | p audio --limit 5
# App
npm run dev        # usa data/dictionary.json (o DICTIONARY_PATH=data/fixtures/dictionary.sample.json)
npm test && (cd scripts && uv run pytest)
```
