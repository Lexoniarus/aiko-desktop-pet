/// <reference lib="webworker" />
import { cleanupOutdatedCaches, precacheAndRoute } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import { packageCachePrefix } from './PackageStore';

declare const self: ServiceWorkerGlobalScope & {
  __WB_MANIFEST: Array<{ url: string; revision: string }>;
};
precacheAndRoute(self.__WB_MANIFEST, {
  ignoreURLParametersMatching: [/^utm_/, /^fbclid$/, /^install$/, /^diagnostics$/],
});
cleanupOutdatedCaches();
registerRoute(
  ({ url }) =>
    url.origin === self.location.origin && url.pathname.includes('/__packages__/'),
  async ({ request, url }) => {
    const id = url.pathname.split('/__packages__/')[1]?.split('/')[0];
    if (!id || !/^[a-f0-9-]{36}$/.test(id))
      return new Response('Invalid package', { status: 400 });
    const cache = await caches.open(packageCachePrefix + id);
    return (
      (await cache.match(request)) ??
      new Response('Package file missing', { status: 404 })
    );
  },
);
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()));
// The installed runtime is never a network fallback. Missing offline files fail
// visibly rather than silently mixing a different application's package version.
