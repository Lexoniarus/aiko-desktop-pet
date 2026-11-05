import { Unzip, UnzipInflate } from 'fflate';
import { activatePackage, packageCachePrefix, packageRoot } from './PackageStore.ts';
import type { InstalledPackage } from './PackageStore';

export interface PackageManifest {
  format: 1;
  protocol: 1;
  saveSchema: number;
  version: string;
  entry: string;
  files: Record<string, { size: number; sha256: string }>;
}
export interface PackageSource {
  size: number;
  stream(): ReadableStream<Uint8Array>;
}
export interface PackageExpectation {
  version: string;
  manifestSHA256: string;
}
export function validPackagePath(path: string): boolean {
  return (
    /^[a-zA-Z0-9_.\-/]+$/.test(path) &&
    !path.startsWith('/') &&
    path.split('/').every((part) => part !== '..' && part !== '.' && part !== '')
  );
}
export function validateManifest(input: unknown): PackageManifest {
  const m = input as Partial<PackageManifest> | null;
  if (
    !m ||
    m.format !== 1 ||
    m.protocol !== 1 ||
    m.saveSchema !== 6 ||
    typeof m.version !== 'string' ||
    !/^[\w.-]{1,80}$/.test(m.version) ||
    typeof m.entry !== 'string' ||
    !validPackagePath(m.entry) ||
    !m.entry.endsWith('.js') ||
    !m.files ||
    typeof m.files !== 'object'
  ) {
    throw new Error('Dieses Paket passt nicht zu diesem Aiko-Starter.');
  }
  const entries = Object.entries(m.files);
  if (!entries.length || entries.length > 12000 || !m.files[m.entry]) {
    throw new Error('Ungültiges Paketverzeichnis.');
  }
  let total = 0;
  for (const [name, file] of entries) {
    if (
      !validPackagePath(name) ||
      !file ||
      !Number.isSafeInteger(file.size) ||
      file.size < 0 ||
      file.size > 64 * 1024 * 1024 ||
      !/^[a-f0-9]{64}$/.test(file.sha256)
    )
      throw new Error('Ungültiger Paketeintrag.');
    total += file.size;
  }
  if (total > 512 * 1024 * 1024) throw new Error('Das Paket ist zu groß.');
  return m as PackageManifest;
}
const mime = (name: string): string =>
  name.endsWith('.js') || name.endsWith('.mjs')
    ? 'text/javascript'
    : name.endsWith('.json')
      ? 'application/json'
      : name.endsWith('.wasm')
        ? 'application/wasm'
        : name.endsWith('.png')
          ? 'image/png'
          : name.endsWith('.css')
            ? 'text/css'
            : 'application/octet-stream';

export async function importPackage(
  file: PackageSource,
  report: (message: string) => void,
  expectation?: PackageExpectation,
): Promise<InstalledPackage> {
  if (
    !Number.isSafeInteger(file.size) ||
    file.size <= 0 ||
    file.size > 300 * 1024 * 1024
  )
    throw new Error('Die ZIP-Datei hat eine ungültige Größe.');
  return navigator.locks.request('aiko-package-install', async () => {
    const id = crypto.randomUUID();
    const cacheName = packageCachePrefix + id;
    const cache = await caches.open(cacheName);
    const root = packageRoot(id);
    let manifest: PackageManifest | undefined;
    let chain = Promise.resolve();
    let failure: unknown;
    const received = new Set<string>();
    let total = 0;
    let compressed = 0;
    let percent = -1;
    let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;
    const unzip = new Unzip((entry) => {
      if (
        !validPackagePath(entry.name) ||
        received.has(entry.name) ||
        received.size >= 12001 ||
        (!received.size && entry.name !== 'manifest.json')
      ) {
        failure = new Error('Unsicherer oder doppelter ZIP-Pfad.');
        return;
      }
      received.add(entry.name);
      const chunks: Uint8Array[] = [];
      let size = 0;
      entry.ondata = (error, data, final) => {
        if (error) {
          failure = error;
          return;
        }
        size += data.length;
        total += data.length;
        if (size > 64 * 1024 * 1024 || total > 514 * 1024 * 1024) {
          failure = new Error('Entpacktes Paket ist zu groß.');
          return;
        }
        chunks.push(data.slice());
        if (!final) return;
        chain = chain.then(async () => {
          if (failure) throw failure;
          const bytes = new Uint8Array(size);
          let offset = 0;
          for (const part of chunks) {
            bytes.set(part, offset);
            offset += part.length;
          }
          chunks.length = 0;
          if (entry.name === 'manifest.json') {
            if (expectation) {
              const digest = await crypto.subtle.digest('SHA-256', bytes);
              const hash = Array.from(new Uint8Array(digest), (value) =>
                value.toString(16).padStart(2, '0'),
              ).join('');
              if (hash !== expectation.manifestSHA256)
                throw new Error(
                  'Das geladene Paket passt nicht zu dieser Einrichtung.',
                );
            }
            manifest = validateManifest(JSON.parse(new TextDecoder().decode(bytes)));
            if (expectation && manifest.version !== expectation.version)
              throw new Error(
                'Die Paketversion stimmt nicht mit der Einrichtung überein.',
              );
            report(`Installiere Aiko ${manifest.version} …`);
            return;
          }
          const expected = manifest?.files[entry.name];
          if (!expected || expected.size !== size)
            throw new Error('Paket ist unvollständig.');
          const digest = await crypto.subtle.digest('SHA-256', bytes);
          const hash = Array.from(new Uint8Array(digest), (b) =>
            b.toString(16).padStart(2, '0'),
          ).join('');
          if (hash !== expected.sha256)
            throw new Error(`Beschädigte Datei: ${entry.name}`);
          await cache.put(
            new URL(entry.name, root),
            new Response(bytes, {
              headers: { 'Content-Type': mime(entry.name) },
            }),
          );
        });
      };
      entry.start();
    });
    unzip.register(UnzipInflate);
    try {
      reader = file.stream().getReader();
      for (;;) {
        const part = await reader.read();
        if (part.done) break;
        compressed += part.value.byteLength;
        if (compressed > file.size)
          throw new Error('Der Paketdownload ist größer als angekündigt.');
        unzip.push(part.value, false);
        await chain;
        const progress = Math.floor((compressed / file.size) * 100);
        if (manifest && progress !== percent) {
          percent = progress;
          report(`Aiko wird eingerichtet: ${progress} %`);
        }
        if (failure) {
          await reader.cancel();
          throw failure;
        }
      }
      unzip.push(new Uint8Array(), true);
      await chain;
      if (failure) throw failure;
      if (compressed !== file.size)
        throw new Error('Der Paketdownload wurde unterbrochen.');
      if (!manifest || received.size !== Object.keys(manifest.files).length + 1) {
        throw new Error('ZIP-Dateien fehlen. Die bisherige Installation bleibt aktiv.');
      }
      const installed = {
        id,
        version: manifest.version,
        entry: manifest.entry,
        installedAt: Date.now(),
      };
      // Storage persistence is a best-effort browser capability. Commit the
      // active pointer last so a refusal cannot delete an activated package.
      try {
        await navigator.storage.persist?.();
      } catch {
        /* Safari may deny persistence; ordinary local storage remains. */
      }
      await activatePackage(installed);
      return installed;
    } catch (error) {
      await reader?.cancel().catch(() => {});
      await caches.delete(cacheName);
      throw error;
    }
  });
}
