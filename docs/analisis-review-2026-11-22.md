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

## Resultado (2026-11-22)

Implementado según `docs/superpowers/plans/2026-11-22-pinyin-hibrido.md` y ejecutado en dos vueltas
(`pinyin` → `review` → `build`):

| | Antes | Vuelta 1 | Vuelta 2 |
|---|---|---|---|
| Palabras visibles | 1739 (70 %) | 2178 (87,1 %) | **2268 (90,7 %)** |
| Issues de la revisión (palabras) | 962 | 397 | 281 |
| …de ellos, de pinyin | 716 | 143 | 27 |
| Frases visibles | 174 | 181 | 181 |

Ningún ejemplo cayó al fallback (`pinyin_fallback` = 0). La segunda vuelta hizo falta porque la
re-revisión (y el sandhi, que cambió el texto de muchos ejemplos) destapó palabras que la primera no
había marcado. Quedan ~254 issues que no son de pinyin (naturalidad, traducción, significado).

### Después de la revisión final de la rama

- Arreglado: el tono neutro de 一/不 que Claude sí había propuesto (对不起 «duì bu qǐ») se perdía; y se rechaza pinyin sin números de tono. Visibles: **2269 (90,8 %)**.
- **Pendiente:** 15 ejemplos visibles aún muestran 对不起 «duì bù qǐ» / 找不到 «zhǎo bú dào». 13 vienen de pypinyin
  (palabras que el revisor IA aprobó sin marcar el tono) y 2 de propuestas que escribieron 不 con tono 4.
  Arreglo propuesto: después de validar, usar las lecturas de palabras de CC-CEDICT presentes en la frase
  (segmentadas con jieba) para fijar los tonos neutros (对不起 = dui4 bu5 qi3, 妈妈 = ma1 ma5). Es
  determinista y también corrige el fallback de pypinyin.
