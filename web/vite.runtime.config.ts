import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  publicDir: false,
  define: { 'process.env.NODE_ENV': JSON.stringify('production') },
  build: {
    outDir: 'dist-runtime',
    target: ['chrome112', 'safari17'],
    lib: {
      entry: 'src/bootstrap.ts',
      formats: ['es'],
      fileName: () => 'app.js',
      cssFileName: 'room',
    },
    rollupOptions: { output: { chunkFileNames: 'chunks/[name]-[hash].js' } },
  },
  worker: { format: 'es' },
});
