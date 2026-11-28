# Palabras de Duolingo

Vocabulario que Sergio ya vio en el curso de chino de Duolingo, cruzado con
`data/dictionary.json`.

| Archivo | Qué es |
|---|---|
| `raw.tsv` | Extracción tal cual: hanzi, pinyin, significado en inglés y unidad (`S1U3` = sección 1, unidad 3). |
| `es_manual.tsv` | Significados en español escritos a mano para las palabras que no están en `dictionary.json`. |
| `palabras.json` | Resultado final (generado, no editar a mano). |

## Cómo se extrae

Duolingo no exporta el vocabulario. Sin Super, la lista de Palabras de la pestaña
Práctica no está disponible, así que la fuente es la pestaña **Caracteres → Hanzi**:
cada carácter desbloqueado abre una ficha con las palabras que lo usan, con pinyin y
significado. Los caracteres en gris aún no están desbloqueados y no traen palabras.

Algunas palabras aparecen sin significado en inglés porque Duolingo no lo muestra en la
ficha. Por eso `meaningEn` puede venir en `null`.

## Actualizar

1. Agrega las filas nuevas a `raw.tsv`.
2. Si alguna palabra no está en `dictionary.json`, agrega su significado a `es_manual.tsv`
   (el script falla con `KeyError` si falta).
3. Corre `python3 scripts/duolingo_build.py`.

Extraído el 28 nov 2026, con la sección 1, unidad 7 en curso.
