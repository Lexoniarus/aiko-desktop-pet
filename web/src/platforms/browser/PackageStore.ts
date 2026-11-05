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

export async function activePackage(): Promise<InstalledPackage | undefined> {
  const db = await packageDatabase();
  try {
    return await new Promise((resolve, reject) => {
      const request = db.transaction('settings').objectStore('settings').get('active');
      request.onsuccess = () => resolve(request.result as InstalledPackage | undefined);
      request.onerror = () => reject(request.error);
    });
  } finally { db.close(); }
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
      };
      tx.oncomplete = () => resolve();
      tx.onabort = () => reject(tx.error ?? new Error('Paketaktivierung abgebrochen.'));
      tx.onerror = () => reject(tx.error);
    });
  } finally { db.close(); }
}

export function packageRoot(id: string): URL {
  return new URL(`__packages__/${encodeURIComponent(id)}/`, new URL('./', location.href));
}
