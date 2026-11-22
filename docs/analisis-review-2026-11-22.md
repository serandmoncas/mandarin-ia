# Análisis de las entradas marcadas por la revisión (2026-11-22)

Fuente: `data/dictionary.json` del build del 2026-10-29.

## Cifras

- El "962" del backlog cuenta **problemas** (issues de la revisión IA), no entradas.
- Entradas ocultas hoy: **829** = 761 palabras + 40 caracteres + 28 frases.
- Las 761 palabras ocultas vienen todas de la revisión IA; ninguna falló un chequeo automático.

| Tipo de problema (palabras) | Issues |
|---|---|
| Pinyin de los ejemplos | **716** (74 %) |
| Naturalidad / gramática del ejemplo | 107 |
| Traducción del ejemplo | 34 |
| Significado de la palabra | 32 |
| Otros (ambigüedad, regionalismos, 小姐…) | ~86 |

Desglose del pinyin: tono neutro en compuestos (妈妈 «mā mā», 喜欢, 时候, 关系) es la mayoría;
le siguen polifónicos según el contexto (得 complemento «de», 长 «cháng», 只 «zhī», 都), erhua
(活儿 «huó ér» en vez de «huór») y sandhi de 一/不 (89).

**Causa raíz:** el pinyin de los ejemplos no lo escribe Claude: lo calcula `sentence_pinyin`
(`scripts/mandarin_pipeline/pinyin.py`) con pypinyin, que no conoce el contexto. A veces
contradice la propia lectura CEDICT de la palabra (妹妹 mei4 mei5 → «mèi mèi»).

**Impacto:** 543 palabras tienen *solo* problemas de pinyin; si se arregla el pinyin, las palabras
visibles pasan de 1739 a **2282 (91,3 %)**, por encima de la meta del 90 %.

## Decisiones (Sergio, 2026-11-22)

1. **Arreglo híbrido.** Claude propone el pinyin numerado de cada ejemplo, con tonos de
   diccionario, tono neutro (5) y erhua. El código valida sílaba por sílaba:
   - se acepta si la sílaba es una lectura de ese carácter en CC-CEDICT, o si coincide con
     la lectura CEDICT de la palabra que lo contiene;
   - se acepta el tono 5 sobre cualquier base válida (tono neutro);
   - 儿 tras otra sílaba puede ser «r» (erhua);
   - si algo no valida, se usa pypinyin para esa frase y se añade el flag `pinyin_fallback`.
   Solo se reprocesan las ~600 palabras con problemas de pinyin y después se re-revisan.
2. **Tono hablado para 一 y 不.** Se aplica sandhi después de validar: 不 ante 4.º tono → bú;
   一 ante 4.º → yí, ante 1.º/2.º/3.º → yì; y se mantiene yī al contar, en ordinales y al final.
   El color de la sílaba sigue el tono hablado. El sandhi del tercer tono **no** se marca
   (la convención es escribir el tono de diccionario).

## Fuera de este arreglo

Los ~160 casos sin pinyin (naturalidad, traducción, significado) necesitan regenerar
ejemplos o revisarlos a mano; se tratan después, junto con la revisión de 20 palabras al azar.
