# Ficha — mandarin-ia

> Fuente de verdad del **qué** y el **por qué** de este proyecto. El estado global
> (activo o estacionado) vive en la cartera:
> `~/Documents/Sam's/200 🧾 Pendientes/Cartera de proyectos.md`.
> El detalle de tareas sigue en `BACKLOG.md`.

- **Tipo:** software

## Intención

Una app en español para aprender mandarín con IA: vocabulario por frecuencia,
repaso espaciado (FSRS), entrenamiento de tonos, reconocimiento de caracteres y
conversación de viaje.

## Para quién

Para Sergio, que todavía **no sabe mandarín**. La app es también su forma de
aprenderlo (Método IA › N13: el agente implementa la lógica de dominio y
explica).

## Promesa / resultado

Conversar en viajes y certificar HSK 3.0 + HSKK a inicios de 2028.

## Apetito

5 sesiones de revisión en este ciclo: crear las cuentas (1), mergear el PR #1
(1) y el primer repaso real usado por Sergio (3).
*(propuesta de Claude, revisar)*

## Fecha de corte

19 dic 2026, la revisión de cierre del ciclo de prueba.

## Criterio de abandono

Si al 19 dic las cuentas de Supabase/Azure siguen sin crearse, el proyecto se
estaciona: sin cuentas no hay audio ni despliegue, y el bloqueo no es técnico.
*(propuesta de Claude, revisar)*

## Dominio (Cynefin)

- **Complicado** en el diccionario y el pinyin: se analiza y se valida contra
  CEDICT.
- **Complejo** en si la app de verdad enseña: solo se sabe cuando Sergio
  estudia con ella.

## No-objetivos

- Contenido más allá de HSK 3 en esta fase.
- Que el Turno Nocturno corra el pipeline: su sandbox bloquea la API.

## Nota de reingreso

- **Dónde está:** Fase 1 en la rama `feat/fase-1-diccionario`, PR #1 abierto
  sin mergear. 2284/2500 palabras visibles (91,4 %).
- **Siguiente acción:** crear las cuentas de Supabase y Azure Speech F0 (pasos en
  `BACKLOG.md` › 1) y probar `audio --limit 5`. Sin cuentas: revisar lo que entregue el
  Turno Nocturno (ver `BACKLOG.md` › Turno Nocturno). El análisis de `review` ya se hizo
  (`docs/analisis-review-2026-11-22.md`).
- **Qué lo bloquea:** las cuentas (Sergio).
