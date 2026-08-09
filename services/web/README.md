# omni-rag — frontend web (React + TypeScript)

Interfaz web mínima para la API de **omni-rag**: escribís una pregunta y ves la
respuesta **con sus citas** y las **fuentes** que la respaldan. También permite
cargar un documento nuevo al índice.

Construida con **Vite + React + TypeScript**. Consume la API de FastAPI del
directorio hermano `../api`.

## Desarrollo

Con la API de omni-rag corriendo en `http://localhost:8000`:

```bash
npm install
npm run dev
```

Abrí la URL que imprime Vite (por defecto http://localhost:5173). En desarrollo,
Vite reenvía las llamadas `/ask`, `/documents` y `/health` al backend, así que no
hay que configurar CORS.

Para apuntar a otra URL de la API (por ejemplo en producción), definí
`VITE_API_URL` antes de `npm run build`.

## Estructura

| Archivo | Qué hace |
|---|---|
| `src/api.ts` | Cliente tipado de la API (`ask`, `ingest`) |
| `src/App.tsx` | UI: formulario de pregunta, respuesta con citas y fuentes |
| `vite.config.ts` | Proxy de desarrollo hacia la API |
