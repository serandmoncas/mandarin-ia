# Diseño — App para aprender mandarín con IA

> Fecha: 2026-10-29 · Estado: borrador para aprobación
> Repo propuesto: `~/Code/mandarin-ia` (nuevo, independiente de KNBK) *(nombre y ubicación: decisión de Claude)*

## 1. Intención y el porqué

Sergio empieza **desde cero** a aprender mandarín. Quiere **viajar y poder hablar**, y además
**certificarse a principios de 2028** (≈14 meses desde hoy). Ninguna app existente junta bien:

- vocabulario ordenado por **frecuencia real de uso**,
- **repaso espaciado**,
- una **IA que sabe qué palabras ya conoces** y conversa/explica **en español**.

Esta app junta esas tres cosas. Empieza siendo para Sergio, pero se construye **multiusuario**
desde el primer día porque la idea es que más personas la usen después.

## 2. Metas, no-metas y anti-metas

**Metas**
- Conversar en situaciones de viaje (restaurante, transporte, hotel, compras, direcciones, emergencias) sin depender del traductor.
- Aprobar **HSK + HSKK** a principios de 2028 (camino "B", elegido por Sergio: oral y escrito).
- Hábito sostenible de **30 min/día**, con **sesiones extra** opcionales cuando él quiera.
- Usable en **celular** (principal) y **computador** (ocasional).
- **Costo cero** mientras el único usuario sea Sergio (decisión de Sergio).

**No-metas (por ahora)**
- Escritura de caracteres a mano (solo **reconocimiento**; ver §7 sobre el formato del examen).
- Caracteres tradicionales / examen TOCFL.
- App nativa en tiendas (App Store / Play Store).
- Cobro, planes de pago, marketing, registro abierto al público.
- Contenido para niveles avanzados (HSK 4+).

**Anti-metas (fracaso aunque "funcione")**
- Gamificación vacía tipo Duolingo: rachas y puntos que premian abrir la app más que aprender.
- Vocabulario de libro poco útil antes que palabras frecuentes.
- Sesiones que se alargan solas: la sesión base **debe** caber en ~30 min.
- Sobrecarga de repasos: las sesiones extra **no** meten palabras nuevas sin control.
- Explicaciones solo en inglés.
- Facturas sorpresa: ningún servicio puede generar cobro sin que Sergio lo active a propósito.

## 3. Restricciones

- Usuario hispanohablante (Colombia); toda la interfaz y explicaciones en **español**.
- **Solo planes gratuitos** en esta etapa (§8). Cada proveedor de IA/voz va detrás de una interfaz
  intercambiable para poder pasar a planes de pago sin rehacer la app.
- Datos con licencia compatible con un uso futuro posiblemente comercial (§6).
- Convenciones de Sergio: identificadores y comentarios en inglés, docs y commits en español,
  Conventional Commits, sin secretos (`.env` + `.env.example`).

## 4. El método (decidido en la conversación)

Principios, en orden de prioridad:
1. **Oír → hablar → leer.** Audio primero, luego pinyin con tonos (coloreados por tono, estilo Pleco), luego carácter.
2. **Tonos desde el día 1**, con entrenamiento perceptivo de pares mínimos (la técnica con más evidencia: ~69 % → 90 % de acierto, sostenido a 6 meses, y transfiere a la producción).
3. **Frases, no palabras sueltas.** Cada palabra se aprende y repasa dentro de una frase corta en la que el resto de palabras, idealmente, ya son conocidas ("i+1"; ver §5.2 cómo se logra).
4. **Caracteres de forma ligera**: solo se presentan caracteres de palabras que el usuario **ya sabe decir**; se explican radicales/componentes en español con una mnemotecnia.
5. **Hablar todos los días**: shadowing (repetir tras el audio) y diálogos con la IA.
6. **Progreso medido por capacidad real**: misiones de viaje superadas y preparación HSK, no puntos.

**Prioridad cuando chocan objetivos** *(decisión de Claude; no hay fecha de viaje, el examen sí tiene fecha)*:
cobertura HSK del nivel objetivo > frecuencia > misiones de viaje.

### 4.1 Sesión diaria base (~30 min)

| Bloque | Min | Contenido |
|--------|-----|-----------|
| 1. Tonos | 4 | Escuchar y elegir entre pares mínimos (mā/má/mǎ/mà, y bisílabos). Feedback inmediato. Dificultad adaptativa. Varias voces. |
| 2. Repaso | 8 | Frases vencidas según FSRS. Audio → ¿entiendes? → significado → repetir en voz alta. |
| 3. Nuevo | 6 | 5–8 palabras nuevas, cada una en frase. Audio, pinyin coloreado, español, carácter. |
| 4. Caracteres | 7 | Reconocer caracteres de palabras ya conocidas (carácter → sonido/significado). Radicales + mnemotecnia en español. |
| 5. Conversación | 5 | Mini-diálogo con la IA dentro de una misión de viaje. Responde por voz o texto; corrección de pronunciación y gramática. |

Los minutos son orientativos; el sistema ajusta la cantidad de ítems para que la sesión quede en
~30 min (si hay muchos repasos vencidos, entran menos palabras nuevas).

**Calificación del repaso** *(decisión de Claude)*: en Repaso y Caracteres el usuario **se autocalifica**
(Otra vez / Difícil / Bien / Fácil, estándar FSRS). Repetir en voz alta en el Repaso **no** se evalúa
con Azure: así el repaso funciona sin conexión y no consume cuota. La evaluación automática de
pronunciación ocurre solo en el bloque de Conversación y en un ejercicio opcional de pronunciación.

**Tarjetas** *(decisión de Claude)*: dos tipos por palabra: **oral** (audio → significado) y
**carácter** (carácter → sonido/significado); la de carácter solo se crea cuando la oral ya está madura.
Las frases de supervivencia de viaje son tarjetas **orales** que se aprenden como bloque completo.

### 4.2 Sesiones extra (a demanda)
El usuario elige: más conversación · historias cortas en audio a su nivel · simulacro HSK/HSKK ·
repaso adelantado. **Regla:** un extra nunca introduce palabras nuevas fuera del límite diario.

### 4.3 Misiones de viaje
Situaciones agrupadas (presentarse, restaurante, transporte, hotel, compras, direcciones, emergencias).
Cada misión tiene sus frases de supervivencia y termina en un **diálogo de prueba** con la IA;
superarlo sin ayuda la marca como lograda.

*(Decisión de Claude)*: las misiones se desbloquean progresivamente. Sus frases se aprenden **como
bloques completos**, aunque contengan palabras que por frecuencia vendrían después, y cuentan dentro del
límite diario de cosas nuevas. Las primeras misiones (presentarse, restaurante) están disponibles desde
la primera semana.

### 4.4 Tablero de progreso
Palabras conocidas · caracteres reconocidos · misiones logradas · barra "listo para HSK N / HSKK".

## 5. Contenido: el diccionario

Es lo primero que se construye (pedido explícito de Sergio).

### 5.1 Capas y entradas
1. **Palabras por frecuencia**: las ~2.500 más frecuentes del habla, cruzadas con la lista oficial
   **HSK 3.0** (niveles 1–3) para que no falte nada del examen.
2. **Frases de supervivencia para viaje**: ~150–200, agrupadas por misión.

**Cada entrada**: simplificado, pinyin (marcas y número), significado en español, nivel HSK 3.0,
rango de frecuencia, audio, 2–3 frases de ejemplo con traducción y, para los caracteres,
componentes + mnemotecnia en español.

### 5.2 Cómo se logra "i+1" sin generar en vivo *(decisión de Claude)*
- **Orden base global**: una secuencia de aprendizaje única (frecuencia + HSK + misiones) calculada en el pipeline.
- **Stock de frases por palabra**: cada palabra tiene varias frases (p. ej. 3–6) generadas en el pipeline,
  escritas usando preferentemente palabras **anteriores** en el orden base.
- **Selección en la app**: al presentar o repasar una palabra, la app elige la frase cuyas otras palabras
  el usuario conoce en mayor proporción. Si el usuario se desvía del orden base (cambia de nivel objetivo,
  ya sabía palabras), la selección lo absorbe.
- Generación en vivo de frases: **no** en esta etapa.

### 5.3 Producción y calidad *(decisión de Claude)*
- El contenido se genera **una vez**, por lotes, con la **suscripción de Claude de Sergio** (sesiones de
  Claude Code ejecutando el pipeline en `scripts/`), y se guarda **versionado en el repo** (JSON/CSV) antes
  de cargarse a la BD. Sin costo de API.
- Sergio no puede revisar chino; por eso la calidad se cuida con **chequeos automáticos**:
  - el pinyin y el significado se contrastan con CC-CEDICT;
  - las frases se segmentan y se verifica que usen las palabras esperadas;
  - un segundo pase de IA revisa naturalidad y la traducción al español.
  - Las entradas que fallan algún chequeo quedan marcadas y no se muestran.
- Cada entrada lleva estado `generated` / `auto_checked` / `human_reviewed`. Se muestran desde `auto_checked`.
- Botón **"Reportar error"** en cada entrada. Una revisión por un nativo o profesor queda para más adelante y no bloquea.

## 6. Fuentes de datos y licencias

| Dato | Fuente | Licencia / nota |
|------|--------|-----------------|
| Definiciones base (inglés), pinyin | **CC-CEDICT** | CC BY-SA 4.0: uso comercial permitido con atribución y *share-alike* sobre ese dato derivado |
| Frecuencia | **wordfreq** (lista `zh`, incluye SUBTLEX-CH) | SUBTLEX-CH oficialmente es "libre para investigación"; wordfreq obtuvo permiso del autor para "cualquier propósito" con atribución. Se usa wordfreq y se acredita SUBTLEX. |
| Lista de examen | **HSK 3.0** (programa oficial publicado nov-2025, rige desde jul-2026) | Lista oficial de vocabulario y caracteres por nivel |
| Audio sintético | **Azure Speech TTS** (plan gratuito, varias voces zh-CN) | Generado una vez, guardado como archivos |
| Audio nativo | **Tatoeba** (complemento) | Solo grabaciones con licencia CC compatible; se filtra por licencia |
| Traducción, frases, mnemotecnias | Claude (suscripción de Sergio) | Generado en el pipeline |

Atribuciones visibles en una página "Créditos".

## 7. Examen objetivo

- HSK 3.0 tiene 9 niveles; su programa rige desde julio 2026, con pilotos desde enero 2026.
  Para 2028 se asume **HSK 3.0**.
- *Estimación de Claude:* con ~220–300 h en 14 meses, la meta realista es **HSK 3.0 nivel 2**
  (nivel 1 seguro, nivel 3 como estiramiento) + **HSKK básico**.
- El nivel objetivo es un parámetro del usuario; cambiarlo no exige rehacer nada.
- **Pendiente de verificar antes de la fase 5** *(no bloquea fases 1–4)*:
  - si en HSK 3.0 bajo se exige escribir caracteres a mano;
  - si el examen en Colombia es en computador (escritura con pinyin) o en papel;
  - si HSKK sigue siendo un examen separado.

  Si hay que escribir a mano, se agrega un bloque de escritura y deja de ser no-meta. Si es en computador, se entrena la selección de caracteres al escribir con pinyin.

## 8. Cómo se construye (decisiones de Claude, delegadas por Sergio)

| Pieza | Elección (gratis) |
|-------|-------------------|
| App | **Next.js (App Router) + TypeScript**, **PWA** instalable, mobile-first |
| Cuentas y datos | **Supabase** plan gratuito (Postgres + Auth + RLS por usuario) |
| Hosting | **Vercel Hobby** (uso no comercial; cambiar de plan si algún día se cobra) |
| Tutor de conversación en vivo | **API de Gemini, plan gratuito**. Sergio acepta que Google pueda usar esas conversaciones. Llamadas solo desde el servidor. |
| Plan B del tutor | Diálogos de misión pregenerados con ramas, si el plan gratuito de Gemini se agota o cambia |
| Voz: audio | Archivos pregenerados (Azure TTS + Tatoeba), servidos estáticos y cacheados por la PWA |
| Voz: corrección de pronunciación | **Azure Speech** plan gratuito (*pronunciation assessment* zh-CN, ~5 h/mes), solo en Conversación y en el ejercicio opcional de pronunciación |
| Voz a texto en conversación | Azure (misma cuota) o Web Speech API del navegador como respaldo |
| Repaso espaciado | **FSRS** (`ts-fsrs`) |
| Pipeline del diccionario | Scripts en `scripts/`, ejecutados con Claude Code |

**Multiusuario** *(decisión de Claude)*:
- esquema y RLS multiusuario desde el día 1;
- registro **solo por invitación**;
- **medidor de uso por usuario** (llamadas a Gemini y segundos de Azure) con un tope configurable. Al llegar al tope, la app degrada con elegancia: diálogos pregenerados, sin evaluación de voz.

**Offline**: diccionario, repaso, tonos, caracteres y audio ya descargado funcionan sin conexión.
Conversación y evaluación de voz requieren conexión.

**Riesgo a validar al empezar la fase 4**: qué tan fino evalúa Azure los **tonos** en mandarín.
Si no basta, se busca otra forma de corregir tonos. La percepción de tonos (bloque 1) no depende de esto.

## 9. Fases

1. **Diccionario**:
   - scaffold del repo;
   - pipeline de datos (frecuencia + HSK 3.0 + CC-CEDICT + traducción, frases y chequeos);
   - audio;
   - vista de búsqueda y navegación en la PWA.
2. **Repaso**: login por invitación + FSRS + bloques Nuevo y Repaso + offline.
3. **Tonos** y **Caracteres**.
4. **Conversación y misiones de viaje** (Gemini + Azure pronunciación + medidor de uso).
5. **Sesiones extra**, tablero de progreso, simulacros HSK/HSKK (tras verificar §7).

## 10. Lo que queda al constructor

- Esquema de BD, estructura de carpetas, librerías de UI, diseño visual.
- Prompts concretos (pipeline y tutor).
- Dificultad adaptativa del bloque de tonos.
- Cantidad exacta de frases por palabra y formato de los archivos del pipeline.
- Valores por defecto del tope de uso.

## 11. Referencias de la investigación

- Plazos realistas en adultos: [Polyglottist](https://www.polyglottistlanguageacademy.com/language-culture-travelling-blog/2025/5/13/why-learning-mandarin-as-an-adult-is-more-doable-than-you-think)
- Entrenamiento de tonos (HVPT): [revisión](https://www.preprints.org/manuscript/202309.1732), [UMN](https://experts.umn.edu/en/publications/high-variability-phonetic-training-facilitates-perception-to-prod/)
- HSK 3.0: [StudyCLI](https://studycli.org/learn-chinese/the-new-hsk), [Shanghai Edu](https://edu.sh.gov.cn/study_en_hsk/20260107/5292266eca744a959c1db43237fbc185.html)
- SUBTLEX-CH / wordfreq: [PLOS ONE](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2880003/), [wordfreq NOTICE](https://cdn.jsdelivr.net/npm/nodewordfreq@0.2.1/NOTICE.md)
