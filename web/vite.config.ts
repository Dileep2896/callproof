/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const API = process.env.CALLPROOF_API ?? 'http://127.0.0.1:8761'

export default defineConfig({
  plugins: [react()],
  server: { port: 5761, strictPort: true, proxy: { '/api': API } },
  preview: { port: 5761, strictPort: true, proxy: { '/api': API } },
  test: { environment: 'jsdom', setupFiles: ['./src/__tests__/setup.ts'], globals: true },
})
