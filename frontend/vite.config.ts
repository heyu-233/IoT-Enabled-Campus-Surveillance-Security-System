import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import path from 'node:path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    fs: {
      allow: [
        fileURLToPath(new URL('.', import.meta.url)),
        path.resolve(__dirname, '../video'),
      ],
    },
    proxy: {
      '/demo-videos': {
        target: 'http://127.0.0.1:5173',
        rewrite: (sourcePath) => sourcePath.replace(/^\/demo-videos/, '/@fs/' + path.resolve(__dirname, '../video').replace(/\\/g, '/')),
      },
      '/api': {
        target: 'http://127.0.0.1:8081',
        changeOrigin: true,
      },
    },
  },
})

