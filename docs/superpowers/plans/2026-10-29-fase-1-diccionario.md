# Fase 1 — Diccionario: plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir el diccionario de ~2.500 palabras (frecuencia + HSK 3.0 niveles 1–3) y ~150–200
frases de viaje, con significado en español, frases de ejemplo, caracteres explicados y audio, y una
PWA para buscarlo y navegarlo.

**Architecture:** Un pipeline en Python (`scripts/mandarin_pipeline/`) descarga las fuentes abiertas,
calcula el orden de aprendizaje y genera el contenido por lotes con `claude -p` (suscripción de Sergio,
sin API). Luego corre chequeos automáticos, sintetiza el audio con Azure (plan gratuito) y lo sube a
Supabase Storage. Escribe un único `data/dictionary.json` versionado. La app Next.js lee ese JSON en el
servidor para generar páginas estáticas, y en el cliente usa un índice de búsqueda compacto
(`public/search-index.json`). En esta fase **no** se usan la base de datos ni el login de Supabase:
entran en la fase 2.

**Tech Stack:**
- App: Next.js (última versión estable, App Router, `src/`), TypeScript, Tailwind, Zod, Vitest + Testing Library, Node 22 LTS.
- Pipeline: Python 3.12 con `uv`, pytest, `wordfreq[cjk]`, `pypinyin`, `jieba`, `pydantic`, `httpx`.

**Spec:** `docs/superpowers/specs/2026-10-29-mandarin-ia-design.md`

**Rama:** `feat/fase-1-diccionario`

## Global Constraints

- Identificadores y comentarios de código en **inglés**; docs y mensajes de commit en **español**; Conventional Commits.
- Toda la interfaz de usuario en **español**. Las rutas visibles van en español (`/palabra/[id]`, `/frases`, `/creditos`).
- Sin secretos en el repo: `.env` ignorado y `.env.example` con todas las variables.
- **Solo planes gratuitos.** Ningún paso puede activar un servicio de pago. Azure Speech usa el plan **F0**.
- Contenido visible solo con `status` ∈ {`auto_checked`, `human_reviewed`}. Lo demás queda en el JSON, pero la app no lo muestra ni lo indexa.
- Candidatos: **todas** las palabras HSK 3.0 de niveles 1–3 presentes en CC-CEDICT, completadas con las más frecuentes (wordfreq `zh`) hasta **2.500** en total.
- Frases de ejemplo: **4 por palabra** generadas, cada una de **≤ 20 caracteres han**.
- Colores de tono (estilo Pleco): 1 `#e53935` · 2 `#fb8c00` · 3 `#43a047` · 4 `#1e88e5` · 5 (neutro) `#9e9e9e`.
- Voces Azure: palabras con 3 voces (`zh-CN-XiaoxiaoNeural`, `zh-CN-YunxiNeural`, `zh-CN-XiaoyiNeural`); ejemplos y frases de viaje con 1 voz (`zh-CN-XiaoxiaoNeural`). Formato `audio-24khz-48kbitrate-mono-mp3`.
- Misiones (ids en inglés, etiqueta en español): `introductions` Presentarse · `restaurant` Restaurante · `transport` Transporte · `hotel` Hotel · `shopping` Compras · `directions` Direcciones · `emergencies` Emergencias.
- Créditos obligatorios: CC-CEDICT (CC BY-SA 4.0), SUBTLEX-CH vía wordfreq, lista HSK (fuente y licencia según `data/SOURCES.md`) y voces de Azure.

## Review Focus

1. **Búsqueda por pinyin escrito de cualquier forma.** "nihao", "ni3hao3", "nǐhǎo", "ni hao" y "NIHAO" deben encontrar 你好. "lv", "lü" y "lu:" deben encontrar 绿. Buscar en español debe ignorar tildes: "cafe" encuentra "café". Tests en Tareas 1 y 9.
2. **Caracteres con varias lecturas y cambios de tono.** 行 tiene varias lecturas en CC-CEDICT: la elegida por la IA debe existir; un índice fuera de rango marca la entrada, no rompe el pipeline. En 不 y 一 se muestra el tono de diccionario. Tests en Tarea 5.
3. **Lote de generación inválido o interrumpido.** Si la respuesta no es JSON válido se reintenta una vez y luego se registra el error. Si se vuelve a ejecutar, salta los lotes ya hechos y continúa. Tests en Tarea 4.
4. **Tokens basura de wordfreq** (latín, dígitos, signos, nombres que no están en CC-CEDICT) se filtran. Una palabra HSK que no esté en CC-CEDICT genera una advertencia, no un error. Tests en Tareas 2 y 3.
5. **Cuota de Azure agotada (HTTP 429) a mitad de corrida.** Se guarda el manifiesto y se sale con un mensaje claro. La siguiente corrida no vuelve a sintetizar lo ya hecho. Tests en Tarea 7.

---

## Estructura de archivos

```
mandarin-ia/
├── CLAUDE.md                         # contexto del repo (convenciones, comandos)
├── .env.example
├── docs/setup.md                     # cuentas gratuitas: Azure F0, Supabase Storage
├── data/
│   ├── SOURCES.md                    # fuentes, versiones, licencias
│   ├── sources/                      # descargas crudas (gitignored)
│   ├── candidates.json               # orden de aprendizaje (versionado)
│   ├── generated/{words,chars,phrases,review}/batch_NNN.json   # versionado
│   ├── audio-manifest.json           # clave → ruta en Storage (versionado)
│   ├── dictionary.json               # salida final (versionado)
│   └── fixtures/dictionary.sample.json  # contrato Python→TS (versionado)
├── scripts/
│   ├── pyproject.toml
│   ├── mandarin_pipeline/
│   │   ├── __main__.py               # CLI argparse: download|candidates|generate|review|audio|build|stats
│   │   ├── sources.py  cedict.py  hsk.py  frequency.py
│   │   ├── order.py    pinyin.py  models.py
│   │   ├── generate.py checks.py  tts.py  build.py
│   │   └── prompts/{words,chars,phrases,review}.md
│   ├── tests/                        # pytest + fixtures/
│   └── build-search-index.ts         # prebuild de la app
└── src/
    ├── app/  page.tsx · palabra/[id]/page.tsx · frases/page.tsx · creditos/page.tsx · manifest.ts · layout.tsx
    ├── components/  PinyinText.tsx · AudioButton.tsx · SearchBox.tsx · WordCard.tsx
    └── lib/  pinyin.ts · dictionary/schema.ts · dictionary/load.ts · search/index.ts
```

## Contrato `dictionary.json` (lo escribe Python y lo lee TS)

```ts
type Tone = 1 | 2 | 3 | 4 | 5;
type Status = "generated" | "auto_checked" | "human_reviewed";
type MissionId = "introductions" | "restaurant" | "transport" | "hotel" | "shopping" | "directions" | "emergencies";
interface Syllable { hanzi: string; pinyin: string; tone: Tone }          // pinyin con marca: "nǐ"
interface AudioRef { voice: string; path: string }                          // path relativo: "a1b2c3d4e5f6a7b8.mp3"
interface Example { zh: string; pinyin: string; syllables: Syllable[]; es: string; knownBeforeRatio: number; audio: AudioRef | null }
interface WordEntry {
  id: string;                    // = simplified
  simplified: string; traditional: string;
  pinyin: string;                // "nǐ hǎo"
  pinyinNumbered: string;        // "ni3 hao3"
  syllables: Syllable[];
  meaningsEs: string[];          // 1–4
  hskLevel: number | null;       // 1–9 o null
  freqRank: number;              // 1 = más frecuente entre los candidatos
  order: number;                 // posición en el orden de aprendizaje, 1-based
  audio: AudioRef[];
  examples: Example[];
  status: Status; flags: string[];
}
interface CharacterInfo { char: string; components: { char: string; meaningEs: string }[]; mnemonicEs: string; status: Status; flags: string[] }
interface PhraseEntry { id: string; mission: MissionId; zh: string; pinyin: string; syllables: Syllable[]; es: string; audio: AudioRef | null; status: Status; flags: string[] }
interface Dictionary { version: string; generatedAt: string; words: WordEntry[]; characters: Record<string, CharacterInfo>; phrases: PhraseEntry[]; credits: { name: string; license: string; url: string }[] }
```

Python serializa en camelCase (alias de pydantic en `models.py`).

---

### Task 1: Scaffold de la app + utilidades de pinyin

**Files:**
- Create: app Next.js en la raíz del repo (`npx create-next-app@latest . --ts --app --src-dir --tailwind --eslint --use-npm --import-alias "@/*"`), `vitest.config.ts`, `CLAUDE.md`, `.env.example`
- Create: `src/lib/pinyin.ts`
- Test: `src/lib/pinyin.test.ts`

**Interfaces:**
- Produces:
  - `normalizeForSearch(s: string): string`: minúsculas; `ü`, `u:` y `v` → `v` *antes* de quitar diacríticos; NFD sin diacríticos; quita dígitos 1–5 pegados a sílabas, espacios, apóstrofes y guiones.
  - `toneColor(tone: Tone): string`: devuelve el hex de Global Constraints.
  - `type Tone`.

- [ ] **Step 1: Crear la rama `feat/fase-1-diccionario`, correr create-next-app e instalar `vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/jest-dom zod tsx`. Script `"test": "vitest run"`.**
- [ ] **Step 2: Escribir `CLAUDE.md`** con: propósito (1 párrafo), enlace al spec, convenciones de Global Constraints, comandos (`npm run dev`, `npm test`, `uv run --directory scripts pytest`, `uv run --directory scripts python -m mandarin_pipeline <cmd>`).
- [ ] **Step 3: Escribir `.env.example`** con `AZURE_SPEECH_KEY=`, `AZURE_SPEECH_REGION=`, `SUPABASE_URL=`, `SUPABASE_SERVICE_ROLE_KEY=`, `NEXT_PUBLIC_AUDIO_BASE_URL=` y un comentario por variable.
- [ ] **Step 4: Escribir el test que falla**

```ts
describe("normalizeForSearch", () => {
  it.each([["nihao"], ["ni3hao3"], ["nǐhǎo"], ["ni hao"], ["NIHAO"], ["ni3 hao3"]])(
    "%s → nihao", (q) => expect(normalizeForSearch(q)).toBe("nihao"));
  it.each([["lv"], ["lü"], ["lu:"], ["lǜ"], ["lv4"]])("%s → lv", (q) => expect(normalizeForSearch(q)).toBe("lv"));
  it("quita tildes del español", () => expect(normalizeForSearch("Café")).toBe("cafe"));
  it("deja intactos los caracteres han", () => expect(normalizeForSearch("你好")).toBe("你好"));
});
describe("toneColor", () => {
  it("usa los colores estilo Pleco", () => {
    expect(toneColor(1)).toBe("#e53935"); expect(toneColor(5)).toBe("#9e9e9e");
  });
});
```

- [ ] **Step 5: `npm test` → FAIL (módulo no existe)**
- [ ] **Step 6: Implementar `src/lib/pinyin.ts`**
- [ ] **Step 7: `npm test` → PASS; `npm run build` → OK**
- [ ] **Step 8: Commit** `feat: crear scaffold de la app y utilidades de pinyin`

---

### Task 2: Pipeline Python, fuentes y parsers

**Files:**
- Create: `scripts/pyproject.toml` (uv, deps del Tech Stack, pytest), `scripts/mandarin_pipeline/{__init__,__main__,sources,cedict,hsk,frequency}.py`, `data/SOURCES.md`
- Modify: `.gitignore` (añadir `data/sources/`, `scripts/.venv/`)
- Test: `scripts/tests/test_cedict.py`, `test_hsk.py`, `test_frequency.py`, `scripts/tests/fixtures/{cedict_sample.txt,hsk_sample.json}`

**Interfaces:**
- Produces:
  - `@dataclass CedictEntry(traditional: str, simplified: str, pinyin_numbered: str, glosses_en: list[str])`.
  - `parse_cedict(lines: Iterable[str]) -> dict[str, list[CedictEntry]]`, con clave `simplified`. Ignora comentarios `#`. Convierte `u:` a `v` en `pinyin_numbered` y pasa las sílabas a minúsculas.
  - `load_hsk(path: Path) -> dict[str, int]`: simplificado → nivel HSK 3.0 más bajo.
  - `is_han_word(s: str) -> bool`: todos los caracteres en `㐀-鿿`.
  - `word_frequency(word: str) -> float` (wordfreq) y `top_frequency_words(n: int, cedict: dict) -> list[str]`: filtra con `is_han_word` y por presencia en `cedict`.
  - `download_sources(dest: Path) -> None`, expuesto en la CLI `download`.

- [ ] **Step 1: Escribir los tests que fallan**
  - `test_parse_cedict_multiple_readings`: con la línea fixture `行 行 [xing2] /to walk/` y `行 行 [hang2] /row/`, `len(result["行"]) == 2`.
  - `test_parse_cedict_umlaut`: `女 女 [nu:3] /woman/` → `pinyin_numbered == "nv3"`.
  - `test_load_hsk_lowest_level`: una palabra con niveles `new-2` y `new-1` → `1`; niveles `old-*` se ignoran.
  - `test_top_frequency_filters_junk`: con `wordfreq` simulado devolviendo `["的", "ok", "123", "，", "张三", "我"]` y `cedict` con `的` y `我`, el resultado es `["的", "我"]`.
- [ ] **Step 2: `uv run --directory scripts pytest` → FAIL**
- [ ] **Step 3: Implementar los módulos.** Fuentes en `download_sources`:
  - CC-CEDICT: `https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz`.
  - HSK: `complete.json` del repo GitHub `drkameleon/complete-hsk-vocabulary`, etiquetas `new-N`.
- [ ] **Step 4: Verificar la fuente HSK** y anotar en `data/SOURCES.md`:
  - la licencia del repo;
  - si corresponde al programa HSK 3.0 revisado de nov-2025 o al de 2021.

  Si es el de 2021, déjalo anotado como limitación conocida; no bloquea.
- [ ] **Step 5: tests → PASS; `python -m mandarin_pipeline download` descarga ambos archivos en `data/sources/`**
- [ ] **Step 6: Commit** `feat: agregar pipeline con parsers de CC-CEDICT, HSK y frecuencia`

---

### Task 3: Candidatos y orden de aprendizaje

**Files:**
- Create: `scripts/mandarin_pipeline/order.py`
- Test: `scripts/tests/test_order.py`

**Interfaces:**
- Consumes: Task 2 (`parse_cedict`, `load_hsk`, `word_frequency`, `top_frequency_words`).
- Produces:
  - `@dataclass Candidate(word: str, frequency: float, hsk_level: int | None, freq_rank: int = 0, order: int = 0)`.
  - `select_candidates(hsk: dict[str,int], cedict: dict, freq_words: list[str], freq: Callable[[str], float], max_level: int = 3, total: int = 2500) -> tuple[list[Candidate], list[str]]`: devuelve los candidatos y las advertencias (palabras HSK que no están en CEDICT).
  - `learning_order(cands: list[Candidate]) -> list[Candidate]`: asigna `freq_rank` y `order`.
  - CLI `candidates` → `data/candidates.json`.

`learning_order`:
1. `freq_rank` = posición 1-based ordenando por `frequency` descendente.
2. `hsk_rank` = posición 1-based ordenando las palabras con `hsk_level` por (nivel, `freq_rank`).
3. Clave de orden = `min(freq_rank, 1.25 * hsk_rank)` (las que no son HSK usan solo `freq_rank`). Desempate por `freq_rank`.

- [ ] **Step 1: Escribir los tests que fallan**
  - `test_includes_all_hsk_up_to_max_level`: las HSK de nivel ≤ 3 están todas y las de nivel 4 no, aunque sean frecuentes.
  - `test_fills_to_total_with_frequent_words`: `len(cands) == total` cuando alcanzan las palabras frecuentes.
  - `test_missing_hsk_word_is_warning`: una palabra HSK ausente de cedict aparece en las advertencias y no en los candidatos.
  - `test_rare_hsk1_word_pulled_forward`: con 100 palabras frecuentes no-HSK y una palabra HSK-1 de frecuencia mínima (`hsk_rank=1`), su `order <= 2`.
  - `test_frequent_non_hsk_stays_early`: la palabra más frecuente tiene `order == 1` cuando no hay HSK más urgente.
  - `test_order_is_dense_1_based`: los `order` forman exactamente `1..N`.
- [ ] **Step 2: FAIL → Step 3: implementar → Step 4: PASS**
- [ ] **Step 5: Ejecutar `python -m mandarin_pipeline candidates` con los datos reales.** Debe imprimir el total (2500), cuántas HSK hay por nivel y las advertencias. Revisar a ojo que las primeras 30 palabras sean comunes (的, 我, 你, 是…).
- [ ] **Step 6: Commit** `feat: calcular candidatos y orden de aprendizaje` (incluye `data/candidates.json`)

---

### Task 4: Generación de contenido por lotes con `claude -p`

**Files:**
- Create: `scripts/mandarin_pipeline/models.py`, `generate.py`, `prompts/{words,chars,phrases}.md`
- Test: `scripts/tests/test_generate.py`

**Interfaces:**
- Consumes: `Candidate`, `CedictEntry`.
- Produces (`models.py`, pydantic):
  - `GeneratedExample(zh: str, es: str)`.
  - `WordContent(word: str, cedict_reading_index: int, meanings_es: list[str] [1..4], examples: list[GeneratedExample] [exactamente 4])`.
  - `CharContent(char: str, components: list[Component(char, meaning_es)], mnemonic_es: str)`.
  - `PhraseContent(mission: MissionId, zh: str, es: str)`.
- Produces (`generate.py`):
  - `Runner = Callable[[str], str]`.
  - `claude_runner(prompt: str) -> str`: ejecuta `claude -p <prompt> --output-format json` y devuelve el campo `result` sin cercas de código.
  - `run_batches(kind: Literal["words","chars","phrases"], items: list[dict], render_prompt: Callable[[list[dict]], str], model: type[BaseModel], runner: Runner, out_dir: Path, batch_size: int = 20) -> BatchReport`, con `BatchReport(done: int, skipped: int, failed: list[int])`.
  - CLI `generate words|chars|phrases [--limit N]`.

Contenido de los prompts (en español; piden **solo** un arreglo JSON):
- **words:** por cada palabra se envía el simplificado, sus lecturas CEDICT numeradas con glosas en inglés y la lista de palabras con `order` menor (vocabulario conocido). Se pide:
  - el índice de la lectura más común;
  - 1–4 significados en español neutro latinoamericano;
  - 4 frases de ≤ 20 caracteres que contengan la palabra y usen preferentemente vocabulario conocido, cada una con su traducción.
- **chars:** caracteres únicos de los candidatos. Para cada uno, sus componentes con significado en español y una mnemotecnia breve en español.
- **phrases:** una llamada por misión, ~25–30 frases de supervivencia de viaje útiles, cortas, con su traducción.

- [ ] **Step 1: Escribir los tests que fallan** (con un runner falso, sin llamar a `claude`)
  - `test_writes_batch_files`: 45 ítems y `batch_size=20` producen `batch_000.json`, `batch_001.json` y `batch_002.json`.
  - `test_resume_skips_existing`: se vuelve a ejecutar con los archivos ya presentes; el runner no se llama y `report.skipped == 3`.
  - `test_invalid_json_retries_once_then_records_error`: el runner devuelve `"no json"` dos veces. Se llamó exactamente 2 veces, existe `batch_000.error.txt` y `report.failed == [0]`, y los demás lotes continúan.
  - `test_schema_violation_counts_as_invalid`: 3 ejemplos en lugar de 4 provoca reintento.
  - `test_strips_code_fences`: una respuesta envuelta en ```` ```json … ``` ```` se parsea bien.
- [ ] **Step 2: FAIL → Step 3: implementar → Step 4: PASS**
- [ ] **Step 5: Prueba real pequeña.** `python -m mandarin_pipeline generate words --limit 20` produce un lote. Revisar a ojo que el español sea natural y que las frases contengan la palabra.
- [ ] **Step 6: Commit** `feat: generar contenido por lotes con claude -p`

---

### Task 5: Chequeos automáticos, revisión por IA y estado

**Files:**
- Create: `scripts/mandarin_pipeline/pinyin.py`, `checks.py`, `prompts/review.md`
- Test: `scripts/tests/test_pinyin.py`, `test_checks.py`

**Interfaces:**
- Consumes: `WordContent`, `CharContent`, `PhraseContent`, `CedictEntry`, `run_batches`, `Runner`.
- Produces (`pinyin.py`):
  - `numbered_to_marked(s: str) -> str`. Regla de la marca: va en `a` o `e` si existen; en `ou` va sobre la `o`; si no, sobre la última vocal. `v` se convierte en `ü`. El tono 5 no lleva marca.
  - `syllables_for(hanzi: str, numbered: str) -> list[Syllable] | None`: devuelve `None` si el número de caracteres y de sílabas no coincide.
  - `sentence_pinyin(zh: str) -> tuple[str, list[Syllable]]`: usa `pypinyin` (`Style.TONE3`, `neutral_tone_with_five=True`) y deja los signos sin sílaba.
- Produces (`checks.py`):
  - `known_before_ratio(zh: str, target: str, known: set[str]) -> float`: segmenta con jieba y calcula la proporción de tokens han que son `target` o están en `known`.
  - `check_word(content: WordContent, entries: list[CedictEntry], known: set[str]) -> CheckedWord`.
  - `CheckedWord(content, reading: CedictEntry | None, examples: list[Example], flags: list[str])`.
  - `apply_review(flags: list[str], review_ok: bool, issues: list[str]) -> tuple[Status, list[str]]`.
  - CLI `review`: corre `run_batches` con `prompts/review.md` sobre lo que ya pasó los chequeos y escribe en `data/generated/review/`.

Reglas de `check_word`, con flags en inglés:
- `reading_index_out_of_range` si el índice no existe; entonces `reading=None`.
- Se descarta el ejemplo que no contiene `target` (subcadena) o que tiene > 20 caracteres han.
- `too_few_examples` si quedan menos de 2.
- `syllable_mismatch` si `syllables_for` devuelve `None`.
- `empty_meaning` si algún significado está vacío.

`apply_review`:
- `auto_checked` si no hay flags y la revisión dio ok.
- Si no, `generated`, y las `issues` de la revisión se suman como `review:<texto>`.

- [ ] **Step 1: Escribir los tests que fallan**
  - `test_numbered_to_marked`: `"ni3 hao3"→"nǐ hǎo"`, `"xue2"→"xué"`, `"gou3"→"gǒu"`, `"lv4"→"lǜ"`, `"liu2"→"liú"`, `"ma5"→"ma"`.
  - `test_polyphonic_reading_selected`: 行 con `cedict_reading_index=1` → `reading.pinyin_numbered == "hang2"`.
  - `test_reading_index_out_of_range_flags`: un índice 7 da la flag y no lanza excepción.
  - `test_citation_tone_for_bu`: 不 con lectura `bu4` → `syllables[0].tone == 4` (sin aplicar cambio de tono).
  - `test_drops_examples_without_target`, `test_drops_long_examples`, `test_too_few_examples_flag`.
  - `test_known_before_ratio`: para `"我喜欢你"`, target `"喜欢"` y `known={"我"}`, el resultado es `2/3`.
  - `test_apply_review_statuses`: sin flags y ok → `auto_checked`; con issues → `generated` más `review:…`.
- [ ] **Step 2: FAIL → Step 3: implementar → Step 4: PASS**
- [ ] **Step 5: Commit** `feat: agregar chequeos automáticos y revisión del contenido`

---

### Task 6: Ensamblar `dictionary.json`

**Files:**
- Create: `scripts/mandarin_pipeline/build.py`
- Create: `data/fixtures/dictionary.sample.json`, generado por un test a partir de los fixtures
- Test: `scripts/tests/test_build.py`

**Interfaces:**
- Consumes: Tasks 3–5 (`Candidate`, `CheckedWord`, `apply_review`, `sentence_pinyin`), y `audio-manifest.json` de la Task 7 si existe; si no existe, `audio` queda vacío o `null`.
- Produces:
  - `build_dictionary(candidates, words: dict[str, CheckedWord], reviews, chars, phrases, manifest: dict[str,str], version: str) -> Dictionary` (pydantic, alias camelCase según el contrato).
  - CLI `build` → `data/dictionary.json`.
  - CLI `stats`: cuenta por estado, por flag y por nivel HSK.
  - Los créditos salen de una constante en `build.py` que refleja `data/SOURCES.md`.

- [ ] **Step 1: Escribir los tests que fallan**
  - `test_build_matches_contract`: la salida serializada tiene las claves camelCase del contrato (`meaningsEs`, `freqRank`, `knownBeforeRatio`…).
  - `test_missing_generation_is_absent`: un candidato sin contenido generado no aparece en `words`; aparece en `stats` como `missing`.
  - `test_audio_paths_from_manifest`: si el manifiesto tiene la clave de (`你好`, Xiaoxiao), `audio` incluye ese `path`.
  - `test_writes_sample_fixture`: escribe `data/fixtures/dictionary.sample.json` con los fixtures: 3 palabras (una `generated` con flag), 2 caracteres y 2 frases.
- [ ] **Step 2: FAIL → Step 3: implementar → Step 4: PASS**
- [ ] **Step 5: Commit** `feat: ensamblar dictionary.json según el contrato`

---

### Task 7: Audio con Azure TTS y subida a Supabase Storage

**Files:**
- Create: `scripts/mandarin_pipeline/tts.py`, `docs/setup.md`
- Test: `scripts/tests/test_tts.py`

**Interfaces:**
- Consumes: `dictionary.json` o los datos chequeados (textos a sintetizar), y las voces de Global Constraints.
- Produces:
  - `audio_key(text: str, voice: str) -> str`: primeros 16 caracteres hex de `sha1(f"{voice}|{text}")`, más `.mp3`.
  - `synthesize(text: str, voice: str, key: str, region: str, client: httpx.Client) -> bytes`: hace `POST https://{region}.tts.speech.microsoft.com/cognitiveservices/v1` con SSML `xml:lang="zh-CN"`.
  - `upload(path: str, data: bytes, supabase_url: str, service_key: str, client) -> None`: hace `POST {url}/storage/v1/object/audio/{path}` con `x-upsert: true`.
  - `run_audio(jobs: list[tuple[str,str]], manifest_path: Path, synth, upload) -> AudioReport`, con `AudioReport(done, skipped, quota_exhausted: bool)`.
  - CLI `audio [--limit N]`.

- [ ] **Step 1: Escribir `docs/setup.md`**, para que Sergio lo haga a mano:
  - crear un recurso Azure Speech **F0** y copiar la clave y la región;
  - verificar en la página de precios de Azure los límites actuales de F0 y anotarlos;
  - crear un proyecto Supabase gratuito con el bucket **público** `audio`;
  - llenar `.env`;
  - `NEXT_PUBLIC_AUDIO_BASE_URL = {SUPABASE_URL}/storage/v1/object/public/audio/`.
- [ ] **Step 2: Escribir los tests que fallan** (con funciones `synth` y `upload` falsas)
  - `test_audio_key_stable`: el mismo texto y voz dan la misma clave; otra voz da otra clave.
  - `test_skips_jobs_in_manifest`.
  - `test_quota_429_stops_and_saves_manifest`: `synth` lanza `QuotaExhausted` en el tercer trabajo. El manifiesto en disco contiene los 2 primeros y `quota_exhausted is True`. En la segunda corrida, `synth` no se llama para esos 2.
  - `test_manifest_saved_every_job`: el manifiesto se escribe tras cada subida; así sobrevive a un Ctrl-C.
- [ ] **Step 3: FAIL → Step 4: implementar (`synthesize` mapea HTTP 429 a `QuotaExhausted`) → Step 5: PASS**
- [ ] **Step 6: Commit** `feat: sintetizar audio con Azure y subirlo a Supabase Storage`

---

### Task 8: Corrida real del pipeline

Tarea operativa: no lleva código nuevo, salvo arreglos que salgan durante la corrida.

- [ ] **Step 1: Confirmar con Sergio** que `docs/setup.md` está hecho y que `.env` existe. Sin eso, ejecutar solo los pasos 2–5 y dejar el audio pendiente.
- [ ] **Step 2: `generate words`** en tandas: varias sesiones si hace falta; el comando continúa solo donde quedó. Luego `generate chars` y `generate phrases`.
- [ ] **Step 3: Reintentar los lotes fallidos.** Borrar los `.error.txt` y volver a ejecutar.
- [ ] **Step 4: `review` → `build` → `stats`.** Objetivo: ≥ 90 % de palabras `auto_checked`. Si queda por debajo, revisar las flags más comunes y ajustar el prompt antes de seguir.
- [ ] **Step 5: Revisión a ojo con Sergio** de 20 palabras al azar: ¿el español es natural?
- [ ] **Step 6: `audio`** (puede tomar más de un mes de cuota gratuita; el comando continúa solo) → `build` otra vez.
- [ ] **Step 7: Commit** `chore: generar contenido del diccionario` (incluye `data/generated/`, `data/dictionary.json` y `data/audio-manifest.json`)

---

### Task 9: Carga del diccionario y búsqueda en la app

**Files:**
- Create: `src/lib/dictionary/schema.ts`, `src/lib/dictionary/load.ts`, `src/lib/search/index.ts`, `scripts/build-search-index.ts`
- Modify: `package.json` (`"prebuild": "tsx scripts/build-search-index.ts"`), `.gitignore` (`public/search-index.json`)
- Test: `src/lib/dictionary/schema.test.ts`, `src/lib/search/index.test.ts`

**Interfaces:**
- Consumes: el contrato, `data/fixtures/dictionary.sample.json` y `normalizeForSearch`.
- Produces:
  - `DictionarySchema` (Zod) y los tipos inferidos `Dictionary`, `WordEntry`, `PhraseEntry`, `CharacterInfo`.
  - `isVisible(e: { status: Status }): boolean`.
  - `loadDictionary(path?: string): Dictionary`, solo en el servidor: lee `data/dictionary.json` y filtra las entradas no visibles.
  - `type SearchDoc = { id: string; kind: "word" | "phrase"; hanzi: string; pinyinKey: string; esKeys: string[]; order: number }`.
  - `buildSearchIndex(d: Dictionary): SearchDoc[]`.
  - `searchEntries(index: SearchDoc[], query: string, limit = 20): SearchDoc[]`.

- [ ] **Step 1: Escribir los tests que fallan**
  - `test schema parses Python fixture`: `DictionarySchema.parse(sampleJson)` no lanza.
  - `test loadDictionary hides non-visible`: la palabra `generated` del fixture no aparece.
  - `test search index excludes hidden entries`.
  - `searchEntries`:
    - "nihao", "ni3hao3", "nǐhǎo" → 你好 primero;
    - "hola" → 你好;
    - "cafe" → la entrada con "café";
    - "你" → 你好;
    - "" → `[]`;
    - con dos coincidencias equivalentes, gana el `order` menor.
- [ ] **Step 2: FAIL**
- [ ] **Step 3: Implementar schema, carga e índice**
- [ ] **Step 4: 🧑‍🎓 Contribución de Sergio: el ranking de `searchEntries`** (5–10 líneas). Claude deja la función con la firma, el filtrado ya hecho y un `TODO`. Sergio decide cómo puntuar:
  - coincidencia exacta de caracteres han;
  - prefijo de pinyin;
  - palabra en español;
  - desempate por `order`.

  Los tests del paso 1 son el piso mínimo.
- [ ] **Step 5: `npm test` → PASS**
- [ ] **Step 6: Commit** `feat: cargar diccionario y buscar por caracteres, pinyin o español`

---

### Task 10: Interfaz: búsqueda, detalle de palabra, frases, créditos y PWA

**Files:**
- Create: `src/components/{PinyinText,AudioButton,SearchBox,WordCard}.tsx`, `src/app/page.tsx`, `src/app/palabra/[id]/page.tsx`, `src/app/frases/page.tsx`, `src/app/creditos/page.tsx`, `src/app/manifest.ts`, íconos en `public/icons/` (192 y 512)
- Test: `src/components/PinyinText.test.tsx`, `src/components/AudioButton.test.tsx`

**Interfaces:**
- Consumes: Task 9 (`loadDictionary`, `searchEntries`, tipos) y `toneColor`.
- Produces:
  - `<PinyinText syllables={Syllable[]} />`: cada sílaba en un `<span>` con `style.color = toneColor(tone)`.
  - `<AudioButton audio={AudioRef} label="string" />`: arma la URL con `process.env.NEXT_PUBLIC_AUDIO_BASE_URL + path`. Si `audio` es `null`, no se renderiza.

Pantallas (mobile-first, en español):
- **Inicio `/`:** buscador (client, carga `/search-index.json` una vez) y lista "Por orden de aprendizaje", paginada de 50 en 50 (`?p=`). Cada `WordCard` muestra carácter, pinyin coloreado, primer significado y nivel HSK.
- **`/palabra/[id]`:** estática, con `generateStaticParams` para las visibles. Muestra:
  - carácter grande, pinyin coloreado y un botón de audio por voz ("Voz 1", "Voz 2", "Voz 3");
  - significados, "HSK N" y "#rango de frecuencia";
  - ejemplos con pinyin coloreado, español y audio;
  - sección "Caracteres", con componentes y mnemotecnia;
  - enlace "Reportar error" a un `mailto:` con el id. Es un placeholder hasta la fase 2.
- **`/frases`:** frases de viaje agrupadas por misión, con etiquetas en español.
- **`/creditos`:** lista `credits` con licencia y enlace.
- **`manifest.ts`:** `name: "Mandarín IA"`, `display: "standalone"`, `lang: "es"` e íconos. Los íconos son un placeholder simple: el carácter 中 sobre un fondo sólido.

- [ ] **Step 1: Escribir los tests que fallan**
  - `PinyinText colors each syllable`: `[{hanzi:"你",pinyin:"nǐ",tone:3},{hanzi:"好",pinyin:"hǎo",tone:3}]` da 2 spans con color `#43a047`.
  - `AudioButton renders nothing without audio`.
- [ ] **Step 2: FAIL → Step 3: implementar componentes y páginas → Step 4: PASS**
- [ ] **Step 5: Verificar a mano.** `npm run build` OK. `npm run dev`, en el celular (misma red) o con DevTools en modo móvil:
  - buscar "nihao" y "hola";
  - abrir una palabra y oír el audio;
  - ver `/frases` y `/creditos`;
  - instalar la PWA.
- [ ] **Step 6: Commit** `feat: agregar interfaz del diccionario e instalación como PWA`

---

### Task 11: Despliegue en Vercel (Hobby)

- [ ] **Step 1: Preguntar a Sergio antes de desplegar** (es una acción visible hacia afuera). Con su sí, vincular el proyecto en Vercel Hobby, configurar `NEXT_PUBLIC_AUDIO_BASE_URL` y desplegar en preview.
- [ ] **Step 2: Verificar la URL de preview desde el celular:** búsqueda, audio e instalación.
- [ ] **Step 3: Marcar la fase 1 como hecha en el spec (§9)** y commit `docs: marcar fase 1 como completada`.

---

## Decisiones de este plan (sobre el spec)

- **Supabase en la fase 1 solo para Storage del audio.** La BD y el login entran en la fase 2, cuando hay progreso por usuario. Mientras tanto la app lee `dictionary.json` estático.
- **Audio de Tatoeba diferido** a una fase posterior. En la fase 1 solo hay voces de Azure.
- **El pinyin de las palabras sale de CC-CEDICT**, no de la IA. **El de los ejemplos sale de `pypinyin`**, y el pase de revisión lo verifica.
- **La caché offline (service worker) va en la fase 2.** En esta fase la PWA solo es instalable.
