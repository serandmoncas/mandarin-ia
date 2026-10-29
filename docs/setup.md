# Configuración de servicios externos

Esto se hace una sola vez, a mano. Solo se usan planes **gratuitos**.

## 1. Azure Speech (voz)

1. Entra al portal de Azure y crea un recurso **Speech** (Servicios de IA).
2. En el nivel de precios elige **Free F0**. **No elijas S0**: es de pago.
3. Región: elige una cercana que ofrezca voces neuronales `zh-CN` (por ejemplo `eastus` o `westus2`).
4. En "Claves y punto de conexión" copia **KEY 1** y el nombre de la **región**.
5. Verifica en la página de precios de Azure Speech los límites actuales de F0 y anótalos aquí.
   Supusimos (**verificar**): ~0,5 M de caracteres/mes de TTS neuronal y ~5 h/mes de voz a texto.
   F0 además limita la tasa (~20 solicitudes cada 60 s). `audio` espacia las solicitudes
   a un máximo de 18 por minuto (unas 3,3 s por clip; 1.000 clips ≈ 1 h) y, ante un HTTP
   429, espera lo que indique `Retry-After` (o 60 s) y reintenta. Si el 429 persiste tras
   3 reintentos, `audio` se detiene limpio: puede ser la cuota mensual agotada **o** una
   limitación de tasa persistente. Vuelve a ejecutarlo más tarde (unos minutos si fue la
   tasa; el mes siguiente si fue la cuota); se retoma donde quedó.

## 2. Supabase Storage (archivos de audio)

1. Crea un proyecto Supabase gratuito.
2. En Storage crea un bucket llamado `audio` y márcalo como **público**.
3. En Project Settings → API copia la **Project URL** y la clave **service_role**.

## 3. Archivo `.env`

1. Copia `.env.example` a `.env` en la raíz del repositorio.
2. Completa:
   - `AZURE_SPEECH_KEY` y `AZURE_SPEECH_REGION` (paso 1).
   - `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` (paso 2).
   - `NEXT_PUBLIC_AUDIO_BASE_URL` = `{SUPABASE_URL}/storage/v1/object/public/audio/`
     (con la barra final).
3. `SUPABASE_SERVICE_ROLE_KEY` es **secreta**: solo para el pipeline local. Nunca la pongas
   en Vercel, en el frontend ni en el repositorio (`.env` está ignorado).

## 4. Generar el audio

```
uv run --directory scripts python -m mandarin_pipeline audio [--limit N]
uv run --directory scripts python -m mandarin_pipeline build
```

`audio` es reanudable; después de ejecutarlo vuelve a correr `build` para adjuntar los audios.
