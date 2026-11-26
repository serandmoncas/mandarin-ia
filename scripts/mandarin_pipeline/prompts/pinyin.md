Eres un experto en fonética del chino mandarín. Para una aplicación de aprendizaje de chino para hispanohablantes necesitas escribir el pinyin numerado de frases de ejemplo.

Para cada una de las $count palabras siguientes se te da la palabra y, debajo, sus frases de ejemplo (una por línea). Escribe el pinyin de cada frase siguiendo estas reglas:

- Una sílaba por cada carácter han, en el mismo orden del texto, separadas por espacios.
- Usa pinyin numerado: el tono va como dígito al final de la sílaba (ma1, ma2, ma3, ma4). Ejemplo: 你好 es "ni3 hao3".
- Escribe los tonos de diccionario de cada carácter. No apliques cambios de tono (sandhi), ni el de 一/不 ni el del tercer tono.
- Las sílabas átonas (neutras) llevan tono 5. Ejemplo: 妈妈 es "ma1 ma5".
- El sufijo erhua (儿) se escribe como `r5`. Ejemplo: 花儿 es "hua1 r5".
- Ignora la puntuación, los dígitos y las letras latinas: no generan sílabas.

Elementos:
$items

Responde ÚNICAMENTE con un arreglo JSON válido de $count objetos, en el mismo orden y con la misma `word` que se te dio, sin texto adicional ni cercas de código. Cada objeto lleva todas las frases de esa palabra, en el mismo orden y con el mismo `zh` exacto. Forma de cada objeto:
{"word": "妈妈", "examples": [{"zh": "妈妈很忙。", "pinyin": "ma1 ma5 hen3 mang2"}]}
