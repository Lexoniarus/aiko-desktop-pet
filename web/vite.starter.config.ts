import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  build: { outDir: 'dist-starter', target: ['chrome112', 'safari17'] },
});
