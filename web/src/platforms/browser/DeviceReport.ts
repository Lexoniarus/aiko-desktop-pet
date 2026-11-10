export interface RoomStartup {
  runtime: unknown;
  packageVersion: string;
  buildTimestamp: number;
  startupMilliseconds: number;
}

type StorageReader = Partial<Pick<StorageManager, 'persisted' | 'estimate'>>;

async function observed<T>(read?: () => Promise<T>): Promise<T | null> {
  try {
    return read ? await read() : null;
  } catch {
    return null;
  }
}

/** Read-only diagnostics: never request a permission or touch the pet save. */
export async function readStorageStatus(storage?: StorageReader) {
  const [persisted, estimate] = await Promise.all([
    observed(storage?.persisted?.bind(storage)),
    observed(storage?.estimate?.bind(storage)),
  ]);
  return {
    persistenceSupported: typeof storage?.persisted === 'function',
    persisted,
    estimateSupported: typeof storage?.estimate === 'function',
    usageBytes: estimate?.usage ?? null,
    quotaBytes: estimate?.quota ?? null,
  };
}

export async function collectDeviceReport(startup: RoomStartup) {
  const displayMode =
    ['fullscreen', 'standalone', 'minimal-ui'].find(
      (mode) => matchMedia(`(display-mode: ${mode})`).matches,
    ) ?? 'browser';
  const viewport = window.visualViewport;
  return {
    format: 1,
    createdAt: new Date().toISOString(),
    browser: navigator.userAgent,
    displayMode,
    standalone: displayMode === 'standalone' || displayMode === 'fullscreen',
    secureContext: isSecureContext,
    serviceWorker: !!navigator.serviceWorker?.controller,
    online: navigator.onLine,
    capabilities: {
      webAssembly: typeof WebAssembly !== 'undefined',
      worker: typeof Worker !== 'undefined',
      indexedDB: 'indexedDB' in globalThis,
      cacheStorage: 'caches' in globalThis,
      webLocks: 'locks' in navigator,
    },
    viewport: {
      width: innerWidth,
      height: innerHeight,
      devicePixelRatio,
      visual: viewport
        ? {
            width: viewport.width,
            height: viewport.height,
            scale: viewport.scale,
            offsetLeft: viewport.offsetLeft,
            offsetTop: viewport.offsetTop,
          }
        : null,
    },
    screen: {
      width: screen.width,
      height: screen.height,
      orientation: screen.orientation?.type ?? null,
    },
    storage: await readStorageStatus(navigator.storage),
    ...startup,
    deviceAcceptance:
      'Nur tatsächlich durchgeführte Schritte im Abnahmeblatt bestätigen. Gerätemodell und Betriebssystem dort ergänzen; Browserangaben können verkürzt sein.',
  };
}

export async function downloadDeviceReport(startup: RoomStartup): Promise<void> {
  const report = await collectDeviceReport(startup);
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' }),
  );
  const link = document.createElement('a');
  link.href = url;
  link.download = 'aiko-geraetebericht.json';
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
