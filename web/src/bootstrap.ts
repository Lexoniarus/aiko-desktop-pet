import './room.css';
import { BrowserRoomClient } from './platforms/browser/BrowserRoomClient';
import { BrowserLifecycle } from './platforms/browser/BrowserLifecycle';
import type { RoomReply } from './bridge/RoomClient';
import type { RoomHostOptions } from './bridge/RoomUpdates';
import { RoomView } from './room/RoomView';
import type { AssetManifest } from './room/RoomView';
import { ObjectDragController } from './input/ObjectDragController';
import { RoomUI } from './ui/RoomUI';
import { element } from './ui/dom';
import type { Command } from './ui/dom';
import { downloadDeviceReport } from './platforms/browser/DeviceReport';

export async function startRoom(
  host: HTMLElement,
  root: string,
  options?: RoomHostOptions,
): Promise<void> {
  const startedAt = performance.now();
  const styles = document.createElement('link');
  styles.rel = 'stylesheet';
  styles.href = new URL('app/room.css', root).href;
  document.head.append(styles);
  const loading = element('p', 'runtime-loading', 'Aiko wird wach …');
  host.replaceChildren(loading);
  const client = new BrowserRoomClient();
  try {
    const [first, assets] = await Promise.all([
      client.initialize(root),
      fetch(new URL('runtime-assets.json', root)).then(
        (response) => response.json() as Promise<AssetManifest>,
      ),
    ]);
    const stage = element('section', 'room-stage');
    stage.setAttribute('aria-label', 'Aikos Zimmer – zum Umschauen wischen');
    host.className = 'aiko-room';
    host.replaceChildren(stage);
    const room = new RoomView(stage, root, assets);
    await room.initialize();
    let ui: RoomUI;
    let closing = false;
    let latest = 0;
    const receive = async (reply: RoomReply): Promise<void> => {
      if (closing || !reply.snapshot || reply.requestId < latest) return;
      latest = reply.requestId;
      options?.setGameOpen(!!reply.snapshot.game);
      ui.update(reply.snapshot);
      await room.update(reply.snapshot);
    };
    const command: Command = async (name, args = {}) => {
      if (closing) return;
      try {
        await receive(await client.command(name, args));
      } catch (error) {
        ui.message(error);
      }
    };
    const drag = new ObjectDragController(room, command, async (name, args = {}) => {
      if (closing) return;
      await receive(await client.command(name, args));
    });
    ui = new RoomUI(host, room, drag, command, options?.updates);
    drag.onError = (error) => ui.message(error);
    room.onPetTap = () => {
      void command('contact');
    };
    await receive(first);
    if (new URL(location.href).searchParams.has('diagnostics')) {
      const report = document.createElement('button');
      report.className = 'diagnostic-report';
      report.textContent = 'Gerätebericht';
      report.addEventListener('click', () =>
        downloadDeviceReport(first.runtime, startedAt),
      );
      host.append(report);
    }
    const lifecycle = new BrowserLifecycle(client, receive, (error) =>
      ui.message(error),
    );
    lifecycle.start();
    options?.registerShutdown(async () => {
      if (closing) return;
      closing = true;
      lifecycle.stop();
      drag.cancel();
      try {
        await client.close(true);
        room.destroy();
      } catch (error) {
        closing = false;
        lifecycle.start();
        throw error;
      }
    });
    window.addEventListener('pagehide', () => drag.cancel());
  } catch (error) {
    await client.close().catch(() => {});
    throw error;
  }
}
