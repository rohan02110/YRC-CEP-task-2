import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  root: '.',
  publicDir: 'public',
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'esbuild',
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        worker: resolve(__dirname, 'src/trap/w.ts')
      },
      output: {
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]'
      }
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/robots.txt': 'http://127.0.0.1:8000',
      '/flag.txt': 'http://127.0.0.1:8000',
      '/.env': 'http://127.0.0.1:8000',
      '/backup': 'http://127.0.0.1:8000',
      '/admin-old': 'http://127.0.0.1:8000'
    }
  }
});
