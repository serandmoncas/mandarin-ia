# Backlog — mandarin-ia

Última actualización: 2026-11-26. Rama de trabajo: `feat/fase-1-diccionario`. Repo público: https://github.com/serandmoncas/mandarin-ia (código MIT, `data/` CC BY-SA 4.0).
Diseño: `docs/superpowers/specs/2026-10-29-mandarin-ia-design.md` · Plan Fase 1: `docs/superpowers/plans/2026-10-29-fase-1-diccionario.md`.

## Estado de la Fase 1 (Diccionario)

- [x] Tareas 1–7, 9 y 10 del plan: pipeline Python, contrato JSON, app Next.js (PWA), búsqueda, ficha de palabra, frases, créditos. Revisión final de la rama: limpia.
- [x] Tarea 8 (parte texto): generación + revisión automática + build ejecutados (2026-10-29).
  - Palabras: 2500 → 1739 `auto_checked` (70 %), 761 ocultas. **Meta ≥90 % no alcanzada.**
  - Caracteres: 1039 → 976 aprobados. Frases: 202 → 174 aprobadas. Entradas con flag `review`: 962.
- [ ] Tarea 8 (parte audio) y Tarea 11 (despliegue): ver abajo.

## Pendiente (en orden)

1. [ ] **Cuentas** (Sergio, guía en `docs/setup.md`). `.env` ya existe vacío (gitignored, chmod 600). Al 2026-11-26 las 5 variables siguen vacías.
   - Cómo llenar el `.env` sin pegar claves en el chat: `! open -e .env` en el prompt de Claude Code; después Claude verifica sin imprimirlas.
   - [ ] Supabase: https://supabase.com/dashboard, login con GitHub (`serandmoncas`) → New project `mandarin-ia`, plan Free, región East US (guardar la contraseña de la BD en el gestor) → Storage → New bucket `audio`, **público** → Project Settings → API: copiar Project URL y `service_role` al `.env`. Explicado paso a paso el 2026-11-24; quedó sin hacer.
   - [ ] Azure Speech: recurso **F0** (nunca S0), región `eastus`; copiar KEY 1 y región al `.env`.
   - [ ] `NEXT_PUBLIC_AUDIO_BASE_URL={SUPABASE_URL}/storage/v1/object/public/audio/` (con barra final).
2. [ ] Prueba de audio: `audio --limit 5`.
3. [x] Analizar las entradas en `review` (2026-11-22): ver `docs/analisis-review-2026-11-22.md`. El 74 % de los problemas es pinyin calculado por pypinyin; arreglarlo lleva al 91 %.
   - [x] Pinyin híbrido + sandhi de 一/不 implementados y ejecutados (2026-11-22): **2268 palabras visibles (90,7 %)**, meta cumplida.
   - [ ] Después: los ~234 issues que no son de pinyin (naturalidad, traducción, significado) y los 36 de pinyin restantes (p. ej. 晚上好: la coincidencia desde la derecha toma 上好).
   - [x] Tonos neutros por palabra CEDICT (2026-11-22): **2284 palabras visibles (91,4 %)**; 对不起/找不到 ya dicen «bu». Ver el análisis.
   - [ ] Antes de una tercera pasada `pinyin`: guardar en cada lote el hash de revisión que respondió, para que no vuelva a pedir palabras ya resueltas (hoy re-pide ~10).
   - [ ] Menores diferidos de la revisión final: una palabra con `pinyin_fallback` nunca vuelve a ser objetivo; el erhua no se une en el camino de pypinyin; 儿 y el sandhi cruzan la puntuación; el orden de lotes falla después de `batch_999`; import local de `sandhi` en `sentence_pinyin` (ciclo por `_mark`); `_pinyin` repite la carga de CEDICT de `_review`.
4. [x] Revisar 20 palabras al azar con Sergio (2026-11-24): las 20 bien en español (semilla 20261122; chino y pinyin revisados por Claude).
5. [ ] Audio completo: `audio` (~16 h a ≤18 clips/min, reanudable) → `build` → commit con `data/audio-manifest.json`.
6. [ ] Tarea 11: despliegue en Vercel Hobby — **solo con aprobación de Sergio**; requiere `NEXT_PUBLIC_AUDIO_BASE_URL` en build.
7. [ ] Integrar la rama: PR #1 abierto el 2026-11-22; mergear cuando Sergio lo apruebe.
8. [ ] Opcional (Sergio): reescribir `scoreMatch` en `src/lib/search/index.ts`.

## Turno Nocturno (puesto el 2026-11-26)

Encargado en la nota `2026-11-26.md` de la bóveda (sección 🌙). El turno no puede correr el pipeline (su sandbox bloquea la API), así que solo lee y entrega en `🌙 Turno Nocturno/<día>/<slug>/`; no toca el repo. Al día siguiente revisar e integrar aquí:

- [ ] Verificar `docs/setup.md` contra la documentación actual de Supabase y Azure (límites reales de F0, nombre actual de la clave `service_role`) y entregar una versión corregida.
- [ ] Clasificar los ~270 issues de revisión que quedan en palabras ocultas y proponer qué hacer con cada grupo.
- [ ] Diseñar el arreglo de 晚上好 («wǎn shàng»: la coincidencia desde la derecha toma 上好) con pruebas pytest, como parche.

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
