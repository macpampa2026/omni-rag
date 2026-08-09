import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// En desarrollo, reenvía las llamadas a la API de omni-rag (FastAPI en :8000),
// así el frontend usa rutas relativas y evitamos problemas de CORS.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/ask': 'http://localhost:8000',
      '/documents': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
