# Pinyin híbrido + sandhi de 一/不 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que el pinyin de los ejemplos sea correcto en contexto (tono neutro, polifónicos, erhua) y muestre el tono hablado de 一/不, para pasar del 70 % al ≥90 % de palabras visibles.

**Architecture:** Una pasada nueva `pinyin` del pipeline pide a `claude -p` el pinyin numerado de los ejemplos de las palabras con problemas de pinyin y lo guarda en `data/generated/pinyin/`. Al chequear, cada propuesta se valida sílaba por sílaba contra las lecturas de CC-CEDICT y de pypinyin; si no valida, se usa pypinyin con el flag `pinyin_fallback`. Al final, siempre, se aplica el sandhi de 一/不. Como cambia el texto revisado, el hash cambia y `review` re-revisa solo esas entradas.

**Tech Stack:** Python 3 + uv, pypinyin, jieba, pydantic, pytest; `claude -p` vía `claude_runner`.

**Spec:** `docs/analisis-review-2026-11-22.md` (decisiones del 2026-11-22).

## Global Constraints

- Identificadores y comentarios en inglés; docs y commits en español (Conventional Commits) con la línea `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Solo planes gratuitos; `claude -p` usa la suscripción local.
- Contenido visible solo con `status` en {`auto_checked`, `human_reviewed`}; cualquier flag automático deja la entrada en `generated`.
- Pinyin numerado en minúsculas, `v` para ü (como `parse_cedict`), tono 5 = neutro.
- El sandhi del tercer tono **no** se marca. El sandhi de 一/不 se aplica a ejemplos y frases de viaje, **no** a la lectura de cabecera de la palabra (queda la de CC-CEDICT, coherente con `pinyinNumbered`).
- `data/generated/*/batch_*.json` existentes no se reescriben (append-only).

## Review Focus

- Ejemplo con dígitos o letras latinas (`我有2个`, `WiFi密码`): las sílabas se alinean solo con caracteres han; la propuesta tiene exactamente una sílaba por han. → test en Task 2.
- Propuesta con ü escrita como `ü`, `u:` o `v`, o con mayúsculas: se normaliza antes de comparar. → test en Task 2.
- Erhua escrita como `r5` tras otra sílaba: válida; `r5` al inicio de la frase: inválida. → test en Task 2.
- El modelo devuelve menos o más ejemplos que los guardados, o un `zh` distinto: esa propuesta se ignora para ese ejemplo (fallback), no rompe el lote. → test en Task 4.
- 一 seguido de un neutro que en realidad es 4.º (`一个` con `ge5`): yí. → test en Task 1.

---

### Task 1: Sandhi de 一/不 (lo escribe Sergio)

**Files:**
- Create: `scripts/mandarin_pipeline/sandhi.py` (stub con `retone` ya hecho y `apply_yi_bu_sandhi` como TODO)
- Test: `scripts/tests/test_sandhi.py` (ya escrito)

**Interfaces:**
- Produces: `apply_yi_bu_sandhi(syllables: list[Syllable]) -> list[Syllable]` — lista nueva, no muta la entrada; solo cambia sílabas de 一 (tono 1) y 不 (tono 4). `retone(s: Syllable, tone: int) -> Syllable`.

- [ ] **Step 1:** Correr `uv run --directory scripts pytest tests/test_sandhi.py -q` → FALLA (`NotImplementedError`).
- [ ] **Step 2:** Implementar `apply_yi_bu_sandhi` hasta que pasen las pruebas.
- [ ] **Step 3:** Correr las pruebas → PASAN. Commit `feat: aplicar sandhi de 一 y 不 al pinyin hablado`.

### Task 2: Validar pinyin propuesto contra CC-CEDICT

**Files:**
- Modify: `scripts/mandarin_pipeline/pinyin.py`
- Test: `scripts/tests/test_pinyin.py`

**Interfaces:**
- Consumes: `CedictEntry` (`cedict.py`), `_split_tone`, `_mark`, `_is_han`.
- Produces:
  - `char_readings(cedict: dict[str, list[CedictEntry]]) -> dict[str, set[str]]` — para cada carácter han, el conjunto de bases sin tono (`"de"`, `"dei"`) de todas sus lecturas: las de sus entradas de un solo carácter en CEDICT, las sílabas de ese carácter en entradas multicarácter y `pypinyin.pinyin(ch, style=Style.NORMAL, heteronym=True)`.
  - `validate_numbered(zh: str, numbered: str, readings: dict[str, set[str]]) -> list[Syllable] | None` — `None` si el número de sílabas ≠ número de han, o si alguna base no está en `readings[ch]`. Acepta tono 1–5 sobre una base válida; `儿` con base `r` solo si no es la primera sílaba (se muestra `r`, tono 5).

- [ ] **Step 1: Tests**

```python
R = {"妈": {"ma"}, "我": {"wo"}, "吃": {"chi"}, "得": {"de", "dei"}, "快": {"kuai"},
     "活": {"huo"}, "儿": {"er"}, "女": {"nv"}, "有": {"you"}, "个": {"ge"}}

def test_validate_accepts_neutral_tone():
    s = validate_numbered("妈妈", "ma1 ma5", R)
    assert [(x.pinyin, x.tone) for x in s] == [("mā", 1), ("ma", 5)]

def test_validate_accepts_contextual_reading():
    assert [x.pinyin for x in validate_numbered("吃得快", "chi1 de5 kuai4", R)] == ["chī", "de", "kuài"]

def test_validate_rejects_unknown_base():
    assert validate_numbered("我", "ni3", R) is None

def test_validate_rejects_count_mismatch():
    assert validate_numbered("妈妈", "ma1", R) is None

def test_validate_ignores_digits_and_latin():
    assert [x.hanzi for x in validate_numbered("我有2个", "wo3 you3 ge4", R)] == ["我", "有", "个"]

def test_validate_normalizes_umlaut_and_case():
    for p in ("nü3", "nu:3", "NV3"):
        assert validate_numbered("女", p, R)[0].pinyin == "nǚ"

def test_validate_erhua():
    assert [x.pinyin for x in validate_numbered("活儿", "huo2 r5", R)] == ["huó", "r"]
    assert validate_numbered("儿", "r5", R) is None

def test_char_readings_includes_multichar_entries():
    cedict = parse_cedict(["媽媽 妈妈 [ma1 ma5] /mom/", "得 得 [de2] /to obtain/"])
    r = char_readings(cedict)
    assert "ma" in r["妈"] and {"de", "dei"} <= r["得"]
```

- [ ] **Step 2:** Correr `uv run --directory scripts pytest tests/test_pinyin.py -q` → FALLAN.
- [ ] **Step 3:** Implementar ambas funciones en `pinyin.py`.
- [ ] **Step 4:** Correr las pruebas → PASAN.
- [ ] **Step 5:** Commit `feat: validar pinyin propuesto contra CC-CEDICT`.

### Task 3: Pasada `pinyin` con claude -p

**Files:**
- Create: `scripts/mandarin_pipeline/prompts/pinyin.md`
- Modify: `scripts/mandarin_pipeline/models.py`, `scripts/mandarin_pipeline/generate.py`, `scripts/mandarin_pipeline/__main__.py`
- Test: `scripts/tests/test_generate.py`

**Interfaces:**
- Consumes: `run_batches`, `claude_runner`, `load_reviews`, `_load_dir`.
- Produces:
  - Modelos `ExamplePinyin(zh: str, pinyin: str)` y `WordPinyin(word: str, examples: list[ExamplePinyin])`; `Kind` incluye `"pinyin"` con clave `"word"` en `_KEY`.
  - `pinyin_targets(gen_dir: Path, review_dir: Path) -> list[dict]` — `[{"word", "examples": [zh, ...]}]` en el orden de los lotes de `words/`, solo para palabras cuyo veredicto más reciente tiene algún issue que case con `r"pinyin|tono|lectura|pronunci|sandhi"` (sin distinguir mayúsculas).
  - `make_pinyin_renderer() -> Callable[[list[dict]], str]`.
  - Subcomando CLI `pinyin [--limit N]`, salida en `data/generated/pinyin/`, lotes de 20, informe con `_finish_batches`.
- Prompt: pedir, por cada frase, pinyin numerado una sílaba por carácter han en el orden del texto; tonos de diccionario (no sandhi de 一/不 ni del 3.º); tono 5 para neutros; erhua como `r5`; ignorar puntuación, dígitos y letras latinas. Respuesta: arreglo JSON de `{"word", "examples": [{"zh", "pinyin"}]}`, mismo orden y mismo `zh`.

- [ ] **Step 1: Tests** — `test_pinyin_targets_selects_words_with_pinyin_issues` (fixture con 3 palabras: una con issue «Pinyin: 妈妈 debe ser…», una con issue de traducción, una ok → solo la primera); `test_pinyin_targets_uses_latest_review` (dos veredictos para la misma id; gana el del lote posterior); `test_run_batches_pinyin_validates_word_key` (runner falso que devuelve otra `word` → lote fallido).
- [ ] **Step 2:** Correr `uv run --directory scripts pytest tests/test_generate.py -q` → FALLAN.
- [ ] **Step 3:** Implementar modelos, `pinyin_targets`, renderer, prompt y subcomando.
- [ ] **Step 4:** Correr las pruebas → PASAN; `uv run --directory scripts python -m mandarin_pipeline pinyin --help` muestra `--limit`.
- [ ] **Step 5:** Commit `feat: agregar la pasada pinyin con claude -p`.

### Task 4: Usar el pinyin validado y el sandhi al chequear

**Files:**
- Modify: `scripts/mandarin_pipeline/checks.py`, `scripts/mandarin_pipeline/pinyin.py`, `scripts/mandarin_pipeline/__main__.py`
- Test: `scripts/tests/test_checks.py`

**Interfaces:**
- Consumes: Task 1 `apply_yi_bu_sandhi`; Task 2 `validate_numbered`, `char_readings`; Task 3 `WordPinyin` y `data/generated/pinyin/`.
- Produces:
  - `sentence_pinyin(zh: str, proposed: str | None = None, readings: dict[str, set[str]] | None = None) -> tuple[str, list[Syllable], bool]` — usa la propuesta si valida; si no, pypinyin; aplica siempre `apply_yi_bu_sandhi`; el `bool` es `True` cuando había propuesta y no validó.
  - `check_word(content, entries, known, proposals: dict[str, str] | None = None, readings: dict[str, set[str]] | None = None)` — `proposals` mapea `zh` → pinyin numerado; añade el flag `pinyin_fallback` una vez si algún ejemplo cayó al fallback.
  - `load_checked_words(gen_dir, cedict, order)` lee `gen_dir/"pinyin"` (si existe) y pasa `proposals` y `char_readings(cedict)`.
  - `check_phrase` usa `sentence_pinyin` sin propuesta (solo sandhi).

- [ ] **Step 1: Tests** — `test_check_word_uses_valid_proposal` (妈妈 con `ma1 ma5` → ejemplo «mā ma», sin flags); `test_check_word_flags_invalid_proposal` (propuesta con base inválida → pinyin de pypinyin + flag `pinyin_fallback`); `test_check_word_ignores_proposal_for_other_sentence` (la propuesta es de otro `zh` → sin flag); `test_sentence_pinyin_applies_sandhi` (`不是` sin propuesta → «bú shì»); `test_review_hash_changes_with_new_pinyin` (el `content_hash` del item cambia al añadir la propuesta).
- [ ] **Step 2:** Correr `uv run --directory scripts pytest -q` → FALLAN las nuevas.
- [ ] **Step 3:** Implementar; actualizar los llamadores de `sentence_pinyin` al nuevo retorno de tres valores.
- [ ] **Step 4:** Correr toda la suite (`pytest` y `npm test`) → PASAN. El fixture `data/fixtures/dictionary.sample.json` se regenera con pytest: revisar el diff (solo cambian pinyin y tonos de 一/不).
- [ ] **Step 5:** Commit `feat: usar el pinyin validado y el sandhi de 一/不 al chequear`.

### Task 5: Ejecutar y medir

**Files:**
- Create: `data/generated/pinyin/batch_*.json`, nuevos `data/generated/review/batch_*.json`
- Modify: `data/dictionary.json`, `docs/analisis-review-2026-11-22.md`, `BACKLOG.md`

- [ ] **Step 1:** `p pinyin --limit 20` y revisar a mano 5 propuestas (妈妈, 得, 儿, 长, 只 si aparecen).
- [ ] **Step 2:** `p pinyin` (todas, ~600 palabras, ~30 lotes); repetir si hay lotes fallidos.
- [ ] **Step 3:** `p review` (solo re-revisa lo que cambió de hash) → `p build` → `p stats`.
- [ ] **Step 4:** Verificar: palabras visibles ≥ 2250 (90 %); contar `pinyin_fallback`; contar issues de pinyin restantes con el script del análisis.
- [ ] **Step 5:** Anotar los resultados en el análisis y el backlog; commit `chore: regenerar pinyin de los ejemplos y re-revisar`.
