import { importPackage, validPackagePath } from './PackageImporter.ts';
import type { InstalledPackage } from './PackageStore';

export interface PublishedPackage {
  format: 1;
  version: string;
  package: string;
  size: number;
  manifestSHA256: string;
  buildTimestamp?: number;
}

export function isNewerPublication(
  installedVersion: string,
  installedTimestamp: number,
  published: Pick<PublishedPackage, 'version' | 'buildTimestamp'>,
): boolean {
  return (
    published.version !== installedVersion &&
    (installedTimestamp === 0 || (published.buildTimestamp ?? 0) > installedTimestamp)
  );
}

export function validatePublishedPackage(value: unknown): PublishedPackage {
  const item = value as Partial<PublishedPackage> | null;
  if (
    !item ||
    item.format !== 1 ||
    typeof item.version !== 'string' ||
    !/^[\w.-]{1,80}$/.test(item.version) ||
    typeof item.package !== 'string' ||
    !validPackagePath(item.package) ||
    !item.package.startsWith('packages/') ||
    !item.package.endsWith('.zip') ||
    !Number.isSafeInteger(item.size) ||
    item.size! <= 0 ||
    item.size! > 300 * 1024 * 1024 ||
    typeof item.manifestSHA256 !== 'string' ||
    !/^[a-f0-9]{64}$/.test(item.manifestSHA256) ||
    (item.buildTimestamp !== undefined &&
      (!Number.isSafeInteger(item.buildTimestamp) || item.buildTimestamp <= 0))
  )
    throw new Error('Die Online-Einrichtung ist nicht korrekt bereitgestellt.');
  return item as PublishedPackage;
}

export async function publishedPackage(): Promise<PublishedPackage | undefined> {
  const response = await fetch(new URL('install.json', new URL('./', location.href)), {
    cache: 'no-store',
    signal: AbortSignal.timeout(10000),
  });
  if (response.status === 404) return undefined;
  if (!response.ok) throw new Error('Die Einrichtung konnte nicht geladen werden.');
  const value: unknown = await response.json();
  if (
    value &&
    typeof value === 'object' &&
    'format' in value &&
    value.format === 1 &&
    'enabled' in value &&
    value.enabled === false
  )
    return undefined;
  return validatePublishedPackage(value);
}

export async function installPublishedPackage(
  item: PublishedPackage,
  report: (message: string) => void,
  destination: 'active' | 'pending' = 'active',
): Promise<InstalledPackage> {
  const address = new URL(item.package, new URL('./', location.href));
  report('Aiko wird heruntergeladen. Bitte für die erste Einrichtung online bleiben …');
  const response = await fetch(address, {
    credentials: 'omit',
    redirect: 'error',
    cache: 'no-store',
    signal: AbortSignal.timeout(10 * 60 * 1000),
  });
  if (!response.ok || !response.body)
    throw new Error('Der Aiko-Download ist nicht erreichbar.');
  const length = response.headers.get('Content-Length');
  if (length !== null && Number(length) !== item.size) {
    await response.body.cancel();
    throw new Error('Der Aiko-Download ist unvollständig bereitgestellt.');
  }
  const stream = response.body;
  return importPackage(
    { size: item.size, stream: () => stream },
    report,
    item,
    destination,
  );
}
