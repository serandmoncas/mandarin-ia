# CLAUDE.md

> Este proyecto sigue el Método IA (`~/Code/metodo-ia/METODO.md`). Lee [`PROYECTO.md`](PROYECTO.md) antes de proponer trabajo.

@AGENTS.md

## Propósito

mandarin-ia es una PWA en español para aprender mandarín (vocabulario por frecuencia,
repaso espaciado, tonos, caracteres y conversación de viaje). La Fase 1 entrega el
diccionario: un pipeline en Python genera `dictionary.json` (palabras, frases de ejemplo,
audio) y la app Next.js lo lee y lo muestra.

Spec de diseño: `docs/superpowers/specs/2026-10-29-mandarin-ia-design.md`
Plan de la fase 1: `docs/superpowers/plans/2026-10-29-fase-1-diccionario.md`

## Convenciones

- Identificadores y comentarios de código en **inglés**; docs y mensajes de commit en **español** (Conventional Commits).
- Toda la interfaz en **español**; rutas visibles en español (`/palabra/[id]`, `/frases`, `/creditos`).
- Sin secretos en el repo: `.env` ignorado, `.env.example` con todas las variables.
- **Solo planes gratuitos**: ningún paso puede activar un servicio de pago (Azure Speech en plan F0).
- Contenido visible solo con `status` en {`auto_checked`, `human_reviewed`}.
- Colores de tono (estilo Pleco): 1 `#e53935`, 2 `#fb8c00`, 3 `#43a047`, 4 `#1e88e5`, 5 `#9e9e9e`.
- Python serializa `dictionary.json` en camelCase; TypeScript lo lee.
- Créditos obligatorios: CC-CEDICT (CC BY-SA 4.0), SUBTLEX-CH vía wordfreq, lista HSK y voces de Azure.

## Comandos

```bash
DICTIONARY_PATH=data/fixtures/dictionary.sample.json npm run dev     # desarrollo con el fixture
DICTIONARY_PATH=data/fixtures/dictionary.sample.json npm run build   # build con el fixture
npm test                                                 # tests (vitest, solo src/)
npm run lint                                             # eslint
uv run --directory scripts pytest                        # tests del pipeline
uv run --directory scripts python -m mandarin_pipeline <cmd>   # ejecutar el pipeline
```

La app lee `data/dictionary.json` salvo que `DICTIONARY_PATH` indique otra ruta. Hasta la
primera ejecución real del pipeline (`generate` → `review` → `build`) ese archivo no
existe: usa `DICTIONARY_PATH=data/fixtures/dictionary.sample.json` (lo regenera `pytest`).
