import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Serverda admin panel https://rendershop.uz/seller/ da ochiladi (build), lokal — http://localhost:5174/
export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/seller/' : '/',
  plugins: [react()],
  server: {
    port: 5174,
    proxy: {
      '/api': 'http://127.0.0.1:8010',
      '/media': 'http://127.0.0.1:8010',
    },
  },
}))
