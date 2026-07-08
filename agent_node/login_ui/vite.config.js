import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // Build output goes to dist/ — Flask serves it from there
  build: { outDir: 'dist' },
  server: {
    port: 5173,
    // Dev proxy: forward /api calls to Flask login_api (port 8080)
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
})
