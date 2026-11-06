import type { RoomHostOptions } from '../../bridge/RoomUpdates';
import { BrowserUpdates } from './BrowserUpdates';

/** Keep cached starters compatible while the current browser runtime owns updates. */
export function browserRuntimeUpdates(
  legacy: RoomHostOptions | undefined,
  version: string,
  buildTimestamp: number,
): RoomHostOptions {
  const owner = new BrowserUpdates(version, buildTimestamp);
  if (legacy) {
    // The cached starter calls these public methods after startRoom returns.
    // Delegate its notice and event wiring, never mutate its private state.
    legacy.updates.subscribe = owner.subscribe.bind(owner);
    legacy.updates.check = owner.check.bind(owner);
    legacy.updates.apply = owner.apply.bind(owner);
  } else {
    owner.start();
  }
  return owner.host;
}
