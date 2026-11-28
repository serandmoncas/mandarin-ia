# Configuración de servicios externos

Esto se hace una sola vez, a mano. Solo se usan planes **gratuitos**.

## 1. Azure Speech (voz)

1. Entra al portal de Azure y crea un recurso **Speech** (Azure Speech, parte de *Foundry Tools*,
   antes "Servicios de IA"). Los nombres del portal están cambiando; si no lo ves, busca "Speech".
2. En el nivel de precios elige **Free F0**. **No elijas S0**: es de pago.
3. Región: `eastus` (recomendada). Ofrece TTS neuronal y las tres voces que usa el pipeline
   (`zh-CN-XiaoxiaoNeural`, `zh-CN-YunxiNeural`, `zh-CN-XiaoyiNeural`) son voces estándar
   disponibles con carácter general. `westus2` también sirve. La clave solo funciona con la región
   donde creaste el recurso.
4. En **Administración de recursos → Claves y punto de conexión** copia **KEY 1** y el nombre de
   la **región** (p. ej. `eastus`).
5. Límites de F0 (verificados el 26 nov 2026, no ajustables):
   - TTS neuronal: **0,5 M de caracteres/mes**. **Ojo: cada carácter chino cuenta como 2**, así que
     equivale a unos **250.000 hanzi/mes**. También cuentan espacios y puntuación (no las etiquetas
     `<speak>` y `<voice>`). El uso se ve en el portal en **Supervisión → Métricas →
     Synthesized Characters**.
   - Voz a texto: 5 h de audio/mes (este proyecto no la usa).
   - Tasa: **20 transacciones cada 60 s** para TTS en tiempo real.
6. Cómo lo maneja `audio`: espacia las solicitudes a un máximo de 18 por minuto (unas 3,3 s por
   clip; 1.000 clips ≈ 1 h) y, ante un HTTP 429, espera lo que indique `Retry-After` (o 60 s) y
   reintenta. Según Microsoft, la mayoría de los 429 de TTS se deben a falta momentánea de
   capacidad del servicio para una voz en la región, no a la cuota. Si el 429 persiste tras
   3 reintentos, `audio` se detiene limpio: puede ser la cuota mensual agotada **o** una limitación
   de tasa persistente. Vuelve a ejecutarlo más tarde (unos minutos si fue la tasa; el mes
   siguiente si fue la cuota); se retoma donde quedó. [VERIFICAR] Qué código devuelve Azure F0
   cuando se agota la cuota mensual (¿429 o 403?): si es 403, `audio` fallará con error en vez de
   detenerse limpio.

## 2. Supabase Storage (archivos de audio)

Los audios viven en el proyecto Supabase de sergiomonsalve.com (`orlniujfwolyinsuezcu`,
`us-west-2`, plan Free) para no ocupar un segundo proyecto gratuito. El pipeline sube por el
**protocolo S3** con claves que solo sirven para Storage: no pueden leer la base de datos
(diario, contactos, suscriptores). Según Supabase, «S3 access keys provide full access to all
S3 operations across all buckets and bypass RLS policies»: también alcanzan el bucket `assets`
del sitio, así que se guardan solo en el `.env` local.

1. Bucket `audio` (creado el 28 nov 2026): **público**, límite de 1 MB por archivo y solo
   `audio/mpeg`. Si hay que recrearlo: **Storage → New bucket** con esos tres ajustes.
2. **Storage → S3**: la conexión S3 debe estar activa. Copia el **Endpoint** y la **Region**.
3. En la misma página, **New access key** (nombre: `mandarin-ia pipeline`). Copia el
   **Access key ID** y el **Secret access key** directo al `.env`: el secreto se muestra una
   sola vez. Si se pierde o se filtra, bórrala ahí mismo y crea otra.
4. Plan Free, compartido con el sitio: 1 GB de almacenamiento y 5 GB de egress al mes. Los
   proyectos Free se pausan tras 1 semana sin actividad (el sitio lo mantiene activo).

## 3. Archivo `.env`

1. Copia `.env.example` a `.env` en la raíz del repositorio.
2. Completa:
   - `AZURE_SPEECH_KEY` y `AZURE_SPEECH_REGION` (paso 1).
   - `SUPABASE_S3_ENDPOINT`, `SUPABASE_S3_REGION`, `SUPABASE_S3_ACCESS_KEY_ID` y
     `SUPABASE_S3_SECRET_ACCESS_KEY` (paso 2).
   - `NEXT_PUBLIC_AUDIO_BASE_URL` = `https://<project_ref>.supabase.co/storage/v1/object/public/audio/`
     (con la barra final).
3. Las claves S3 y la de Azure son **secretas**: solo para el pipeline local. Nunca en Vercel,
   en el frontend ni en el repositorio (`.env` está ignorado).

## 4. Generar el audio

```
uv run --directory scripts python -m mandarin_pipeline audio [--limit N]
uv run --directory scripts python -m mandarin_pipeline build
```

`audio` es reanudable; después de ejecutarlo vuelve a correr `build` para adjuntar los audios.
Para la primera vez usa `--limit 1` y comprueba que el archivo aparece en el bucket y se oye
desde `NEXT_PUBLIC_AUDIO_BASE_URL`.
