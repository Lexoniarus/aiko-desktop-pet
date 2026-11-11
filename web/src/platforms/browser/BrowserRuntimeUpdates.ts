import type { RoomHostOptions } from '../../bridge/RoomUpdates';
import { BrowserUpdates } from './BrowserUpdates.ts';

/** Keep cached starters compatible while the current browser runtime owns updates. */
export function browserRuntimeUpdates(
  legacy: RoomHostOptions | undefined,
  version: string,
  buildTimestamp: number,
): RoomHostOptions {
  const owner = new BrowserUpdates(version, buildTimestamp);
  if (legacy) {
    // Cached starters can still call check() on startup and browser events.
    // Settings use the separate runtime owner's check() for explicit requests.
    legacy.updates.subscribe = owner.subscribe.bind(owner);
    legacy.updates.check = () => Promise.resolve();
    legacy.updates.apply = owner.apply.bind(owner);
  }
  return owner.host;
}
