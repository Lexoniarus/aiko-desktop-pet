import './styles.css';
import { activePackage, packageRoot } from './platforms/browser/PackageStore';
import { importPackage } from './platforms/browser/PackageImporter';

const host = document.querySelector<HTMLElement>('#app')!;
host.innerHTML = `<section class="installer"><h1>Aikos Zimmer</h1>
  <p id="install-status" role="status">Installation vorbereiten …</p>
  <p id="install-help">Öffne diesen Starter in Safari und wähle „Zum Home-Bildschirm“.
  Starte Aiko anschließend über ihr Symbol und wähle die ZIP-Datei aus „Dateien“.
  Du kannst sie vorher aus Dropbox oder GitHub herunterladen.</p>
  <label class="button">Aiko-Paket auswählen<input id="package" type="file" accept=".zip,application/zip"></label>
  <button id="start" hidden>Zimmer öffnen</button></section>`;
const installer = host.firstElementChild!;
const status = document.querySelector<HTMLElement>('#install-status')!;
const input = document.querySelector<HTMLInputElement>('#package')!;
const start = document.querySelector<HTMLButtonElement>('#start')!;
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
    await module.startRoom(host, root.href);
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
    throw new Error('Bitte den HTTPS-Starter in einem aktuellen Safari öffnen.');
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
  const installed = await activePackage();
  start.hidden = !installed;
  report(
    installed ? `Aiko ${installed.version} ist bereit.` : 'Wähle dein Aiko-Paket.',
  );
  if (installed && !new URL(location.href).searchParams.has('install')) await launch();
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
void prepare().catch((error) =>
  report(error instanceof Error ? error.message : String(error)),
);
