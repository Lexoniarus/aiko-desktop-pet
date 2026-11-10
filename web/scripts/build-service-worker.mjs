import { build } from 'vite';
import { injectManifest } from 'workbox-build';

await build({
  configFile: false,
  publicDir: false,
  define: { 'process.env.NODE_ENV': JSON.stringify('production') },
  build: {
    target: ['chrome112', 'safari17'],
    outDir: 'dist-sw',
    lib: {
      entry: 'src/platforms/browser/service-worker.ts',
      formats: ['iife'],
      name: 'AikoOffline',
      fileName: () => 'sw.js',
    },
  },
});
await injectManifest({
  swSrc: 'dist-sw/sw.js',
  swDest: 'dist-starter/sw.js',
  globDirectory: 'dist-starter',
  globPatterns: ['**/*.{js,css,html,png,webmanifest}'],
  globIgnores: ['sw.js'],
  maximumFileSizeToCacheInBytes: 4 * 1024 * 1024,
});
