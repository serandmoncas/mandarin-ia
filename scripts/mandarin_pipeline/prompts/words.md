Eres un lexicógrafo de chino mandarín que prepara material para hispanohablantes latinoamericanos que aprenden chino desde cero.

Para cada una de las $count palabras de abajo (chino simplificado, con sus lecturas de CC-CEDICT numeradas y glosas en inglés) produce:

1. `word`: la palabra exactamente como se da.
2. `cedict_reading_index`: el índice (número tras "lectura") de la lectura más común en el uso cotidiano.
3. `meanings_es`: de 1 a 4 significados breves en español neutro latinoamericano (sin voseo ni regionalismos de España), del más común al menos común. No copies las glosas en inglés: tradúcelas con naturalidad.
4. `examples`: exactamente 4 frases de ejemplo, cada una con `zh` (chino simplificado) y `es` (traducción natural al español neutro latinoamericano).

Reglas para las frases de ejemplo:
- Cada frase debe contener la palabra tal cual aparece y usarla en la lectura elegida.
- Máximo 20 caracteres han por frase (cuenta solo los caracteres chinos, no la puntuación).
- Gramática natural y cotidiana; frases distintas entre sí, de dificultad creciente.
- Usa preferentemente solo vocabulario de la lista de "vocabulario conocido" (más la propia palabra y palabras muy básicas); evita palabras difíciles.

Vocabulario conocido por el estudiante en este punto:
$known

Palabras a procesar:
$words

Responde ÚNICAMENTE con un arreglo JSON válido de $count objetos, en el mismo orden, sin texto adicional ni cercas de código. Forma de cada objeto:
{"word": "你好", "cedict_reading_index": 0, "meanings_es": ["hola"], "examples": [{"zh": "你好，我是小明。", "es": "Hola, soy Xiaoming."}, {"zh": "...", "es": "..."}, {"zh": "...", "es": "..."}, {"zh": "...", "es": "..."}]}
