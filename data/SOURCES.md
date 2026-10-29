# Fuentes de datos

Los archivos crudos se descargan con `uv run --directory scripts python -m mandarin_pipeline download`
a `data/sources/` (ignorado por git). La descarga es idempotente: si el archivo existe, se omite.

## CC-CEDICT (diccionario chino-inglés)

- URL: https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz
- Licencia: **CC BY-SA 4.0** (atribución obligatoria; las obras derivadas se comparten bajo la misma licencia).
- Se descomprime a `data/sources/cedict_ts.txt` (el `.gz` se elimina tras descomprimir).
- Uso: pinyin numerado, forma tradicional y glosas en inglés (base para las traducciones al español).

## Lista HSK 3.0 (complete-hsk-vocabulary)

- Repo: https://github.com/drkameleon/complete-hsk-vocabulary, archivo `complete.json` (rama `main`).
- Licencia verificada: **MIT** (LICENSE, Copyright (c) 2026 Yanis Zafirópulos). Se acredita en `/creditos`.
- Niveles: etiquetas `new-1`..`new-7` (HSK 3.0; `new-7` = niveles 7-9) y `old-*` (HSK 2.0, ignoradas).
- Las listas HSK 3.0 provienen de https://github.com/elkmovie/hsk30, extraídas por OCR del PDF oficial del
  Ministerio de Educación publicado en **marzo de 2021**.
- **Limitación conocida:** corresponde al programa HSK 3.0 de **2021**, no a la revisión de nov-2025.
  El repo no menciona esa revisión. Los niveles 1-3 acumulados tienen 2209 palabras (el oficial 2021 tiene
  2245, por diferencias de formas/variantes); 2201 de ellas están en CC-CEDICT. No bloquea la fase 1.

## Frecuencia: wordfreq / SUBTLEX-CH

- Paquete Python `wordfreq[cjk]` (requiere jieba para tokenizar zh); API `top_n_list('zh', n)`.
- Los datos chinos proceden de SUBTLEX-CH (Cai y Brysbaert, 2010) y otras fuentes. wordfreq permite su uso
  "para cualquier propósito" con crédito a los autores de SUBTLEX. Se acredita en `/creditos`.
- Los datos van incluidos en el paquete; no se descargan en `download`.
