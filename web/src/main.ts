import './styles.css';
import {
  activePackage,
  activatePendingPackage,
  packageRoot,
} from './platforms/browser/PackageStore';
import { BrowserUpdates } from './platforms/browser/BrowserUpdates';
import { importPackage } from './platforms/browser/PackageImporter';
import {
  publishedPackage,
  installPublishedPackage,
} from './platforms/browser/PublishedPackage';

const host = document.querySelector<HTMLElement>('#app')!;
host.innerHTML = `<section class="installer"><h1>Aikos Zimmer</h1>
  <p id="install-status" role="status">Installation vorbereiten …</p>
  <p id="install-help">Aiko prüft, ob ihr Paket schon auf diesem Gerät eingerichtet ist.</p>
  <button id="retry" hidden>Einrichtung erneut versuchen</button>
  <label id="manual" class="button" hidden>Aiko-Paket auswählen<input id="package" type="file" accept=".zip,application/zip"></label>
  <button id="start" hidden>Zimmer öffnen</button></section>`;
const installer = host.firstElementChild!;
const status = document.querySelector<HTMLElement>('#install-status')!;
const input = document.querySelector<HTMLInputElement>('#package')!;
const start = document.querySelector<HTMLButtonElement>('#start')!;
const retry = document.querySelector<HTMLButtonElement>('#retry')!;
const manual = document.querySelector<HTMLElement>('#manual')!;
const help = document.querySelector<HTMLElement>('#install-help')!;
let installing = false;
const report = (text: string) => {
  status.textContent = text;
};
async function launch(): Promise<void> {
  const installed = await activePackage();
  if (!installed) return;
  start.disabled = true;
  try {
    const root = packageRoot(installed.id);
    const module = await import(/* @vite-ignore */ new URL(installed.entry, root).href);
    const updates = new BrowserUpdates(installed.version);
    await module.startRoom(host, root.href, updates.host);
    // Outside #app: the already installed runtime replaces that element's children
    // and knows nothing about updates. It can still display this first-upgrade notice.
    const notice = document.createElement('aside');
    notice.className = 'update-notice';
    notice.setAttribute('aria-label', 'App-Update');
    const message = document.createElement('p');
    const restart = document.createElement('button');
    restart.textContent = 'Jetzt neu starten';
    restart.onclick = () => {
      void updates.apply();
    };
    notice.append(message, restart);
    document.body.append(notice);
    updates.subscribe((state) => {
      notice.hidden = !['ready', 'applying'].includes(state.phase);
      message.textContent = state.message;
      restart.hidden = !state.canRestart;
    });
    updates.start();
    const locationURL = new URL(location.href);
    locationURL.searchParams.delete('install');
    history.replaceState(null, '', locationURL);
  } catch (error) {
    host.replaceChildren(installer);
    start.disabled = false;
    report(
      `Aiko konnte nicht starten: ${error instanceof Error ? error.message : String(error)}`,
    );
  }
}
async function prepare(): Promise<void> {
  if (!isSecureContext || !('serviceWorker' in navigator) || !navigator.locks) {
    throw new Error(
      'Die geschützte App-Umgebung mit lokalem Speicher ist nicht verfügbar.',
    );
  }
  await navigator.serviceWorker.register('./sw.js', { scope: './' });
  await navigator.serviceWorker.ready;
  if (!navigator.serviceWorker.controller) {
    await new Promise<void>((resolve) =>
      navigator.serviceWorker.addEventListener('controllerchange', () => resolve(), {
        once: true,
      }),
    );
  }
  await activatePendingPackage();
  const installed = await activePackage();
  start.hidden = !installed;
  report(
    installed ? `Aiko ${installed.version} ist bereit.` : 'Wähle dein Aiko-Paket.',
  );
  if (installed && !new URL(location.href).searchParams.has('install')) {
    await launch();
    return;
  }
  if (!installed) {
    const published = await publishedPackage();
    if (published) {
      if (installing) return;
      installing = true;
      retry.hidden = true;
      manual.hidden = true;
      help.textContent =
        'Die erste Einrichtung braucht Internet. Danach bleiben Aiko und ihr Spielstand auf diesem Gerät verfügbar.';
      try {
        await installPublishedPackage(published, report);
        report('Aiko ist eingerichtet und wird gestartet …');
        start.hidden = false;
        await launch();
      } finally {
        installing = false;
      }
      return;
    }
  }
  manual.hidden = false;
  help.textContent =
    'Wähle für diese Installation die heruntergeladene Aiko-Paketdatei aus. Die ZIP-Datei bleibt unverändert; du musst sie nicht entpacken.';
}
input.addEventListener('change', async () => {
  const file = input.files?.[0];
  if (!file) return;
  input.disabled = true;
  start.disabled = true;
  try {
    const installed = await importPackage(file, report);
    report(`Aiko ${installed.version} ist installiert.`);
    start.hidden = false;
    start.disabled = false;
    await launch();
  } catch (error) {
    report(error instanceof Error ? error.message : String(error));
    start.disabled = false;
  } finally {
    input.disabled = false;
    input.value = '';
  }
});
start.addEventListener('click', () => {
  void launch();
});
function setup(): void {
  void prepare().catch((error) => {
    retry.hidden = false;
    report(
      `Einrichtung nicht abgeschlossen: ${error instanceof Error ? error.message : String(error)} Bitte die Internetverbindung prüfen und erneut versuchen.`,
    );
  });
}
retry.addEventListener('click', setup);
setup();
