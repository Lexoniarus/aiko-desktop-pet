import { defineConfig } from 'vite';

export default defineConfig({
  base: './', publicDir: false,
  build: {
    outDir: 'dist-runtime', target: 'safari17',
    lib: { entry: 'src/bootstrap.ts', formats: ['es'], fileName: () => 'app.js' },
    rollupOptions: { output: { chunkFileNames: 'chunks/[name]-[hash].js' } },
  },
  worker: { format: 'es' },
});
