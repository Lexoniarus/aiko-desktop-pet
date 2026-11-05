import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  build: { outDir: 'dist-starter', target: 'safari17' },
});
