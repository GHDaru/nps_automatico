import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/chamados': {
        target: 'http://localhost:5020',
        changeOrigin: true,
      },
      '/prompts': {
        target: 'http://localhost:5020',
        changeOrigin: true,
      },
      '/campos': {
        target: 'http://localhost:5020',
        changeOrigin: true,
      },
    },
  },
})
