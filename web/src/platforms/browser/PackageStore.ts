export interface InstalledPackage {
  id: string;
  version: string;
  entry: string;
  installedAt: number;
}

const databaseName = 'aiko-room-packages';
export const packageCachePrefix = 'aiko-room-package-';

export function packageDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(databaseName, 1);
    request.onupgradeneeded = () => request.result.createObjectStore('settings');
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onblocked = () => reject(new Error('Bitte andere Aiko-Fenster schließen.'));
  });
}

async function storedPackage(key: string): Promise<InstalledPackage | undefined> {
  const db = await packageDatabase();
  try {
    return await new Promise((resolve, reject) => {
      const request = db.transaction('settings').objectStore('settings').get(key);
      request.onsuccess = () => resolve(request.result as InstalledPackage | undefined);
      request.onerror = () => reject(request.error);
    });
  } finally {
    db.close();
  }
}

export const activePackage = (): Promise<InstalledPackage | undefined> =>
  storedPackage('active');
export const pendingPackage = (): Promise<InstalledPackage | undefined> =>
  storedPackage('pending');

export async function stagePackage(value: InstalledPackage): Promise<void> {
  const db = await packageDatabase();
  try {
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction('settings', 'readwrite');
      tx.objectStore('settings').put(value, 'pending');
      tx.oncomplete = () => resolve();
      tx.onabort = tx.onerror = () => reject(tx.error);
    });
  } finally {
    db.close();
  }
}

export async function activatePackage(value: InstalledPackage): Promise<void> {
  const db = await packageDatabase();
  try {
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction('settings', 'readwrite');
      const store = tx.objectStore('settings');
      const previous = store.get('active');
      previous.onsuccess = () => {
        if (previous.result) store.put(previous.result, 'previous');
        store.put(value, 'active');
        store.delete('pending');
      };
      tx.oncomplete = () => resolve();
      tx.onabort = () => reject(tx.error ?? new Error('Paketaktivierung abgebrochen.'));
      tx.onerror = () => reject(tx.error);
    });
  } finally {
    db.close();
  }
}

// Never switch packages or prune files while a runtime owns the pet database.
// A second window must not change the program beneath an existing session.
export async function activatePendingPackage(): Promise<boolean> {
  return navigator.locks.request(
    'aiko-pet-writer',
    { ifAvailable: true },
    async (writer) => {
      if (!writer) return false;
      return navigator.locks.request(
        'aiko-package-install',
        { ifAvailable: true },
        async (installer) => {
          if (!installer) return false;
          const pending = await pendingPackage();
          if (pending) await activatePackage(pending);
          const preserved = await Promise.all(
            ['active', 'previous', 'pending'].map(storedPackage),
          );
          const keep = new Set(
            preserved
              .filter((item) => !!item)
              .map((item) => packageCachePrefix + item.id),
          );
          for (const name of await caches.keys()) {
            if (name.startsWith(packageCachePrefix) && !keep.has(name))
              await caches.delete(name);
          }
          return !!pending;
        },
      );
    },
  );
}

export function packageRoot(id: string): URL {
  return new URL(
    `__packages__/${encodeURIComponent(id)}/`,
    new URL('./', location.href),
  );
}
