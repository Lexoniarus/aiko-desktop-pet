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
    // The cached starter calls these public methods after startRoom returns.
    // Its event throttle uses stale private state after delegation, so enforce
    // the interval in the runtime owner. Settings use owner.host's manual check.
    legacy.updates.subscribe = owner.subscribe.bind(owner);
    legacy.updates.check = owner.checkAutomatically.bind(owner);
    legacy.updates.apply = owner.apply.bind(owner);
  } else {
    owner.start();
  }
  return owner.host;
}
