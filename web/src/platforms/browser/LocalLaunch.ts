import { activePackage, packageRoot } from './PackageStore.ts';
import type { InstalledPackage } from './PackageStore';
import {
  installPublishedPackage,
  isNewerPublication,
  publishedPackage,
} from './PublishedPackage.ts';

type LocalSelection =
  | { state: 'ready'; installed: InstalledPackage }
  | { state: 'busy' }
  | { state: 'failed'; reason: string; installed?: InstalledPackage; offered?: string };

export function isLocalLaunch(url: URL): boolean {
  return (
    url.origin === 'http://127.0.0.1:8940' &&
    url.pathname === '/' &&
    url.searchParams.get('local-launch') === '1'
  );
}

async function installedTimestamp(installed: InstalledPackage): Promise<number> {
  const response = await fetch(
    new URL('runtime-assets.json', packageRoot(installed.id)),
  );
  if (!response.ok)
    throw new Error('Die Versionsdaten der installierten Version fehlen.');
  const { packageVersion, buildTimestamp } = await response.json();
  if (
    packageVersion !== installed.version ||
    !Number.isSafeInteger(buildTimestamp) ||
    buildTimestamp <= 0
  )
    throw new Error('Die installierte Version lässt sich zeitlich nicht einordnen.');
  return buildTimestamp;
}

export function selectLocalPackage(
  report: (message: string) => void,
): Promise<LocalSelection> {
  return navigator.locks.request(
    'aiko-pet-writer',
    { ifAvailable: true },
    async (writer): Promise<LocalSelection> => {
      if (!writer) return { state: 'busy' };
      let installed: InstalledPackage | undefined;
      let offered: string | undefined;
      try {
        installed = await activePackage();
        const published = await publishedPackage();
        if (!published) throw new Error('Es ist kein lokales Paket angeboten.');
        offered = published.version;
        if (installed?.version === offered) return { state: 'ready', installed };
        if (!published.buildTimestamp)
          throw new Error('Für das lokale Paket fehlt die Build-Zeit.');
        if (
          installed &&
          !isNewerPublication(
            installed.version,
            await installedTimestamp(installed),
            published,
          )
        )
          throw new Error(
            'Das lokale Paket ist nicht neuer als die installierte Version.',
          );
        return {
          state: 'ready',
          installed: await installPublishedPackage(published, report),
        };
      } catch (error) {
        return {
          state: 'failed',
          reason: error instanceof Error ? error.message : String(error),
          installed,
          offered,
        };
      }
    },
  );
}
