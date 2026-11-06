/// <reference lib="webworker" />
import type { PyodideInterface } from 'pyodide';
import { roomProtocol } from '../../bridge/commands';

declare const self: DedicatedWorkerGlobalScope;
let python: PyodideInterface;
let session: { dispatch_json: (message: string) => string } | undefined;
let dirty = false;
function sync(populate: boolean): Promise<void> {
  return new Promise((resolve, reject) =>
    python.FS.syncfs(populate, (error: Error | null) =>
      error ? reject(error) : resolve(),
    ),
  );
}
async function initialize(root: string): Promise<void> {
  const { loadPyodide } = await import(
    /* @vite-ignore */ new URL('runtime/pyodide.mjs', root).href
  );
  python = await loadPyodide({ indexURL: new URL('runtime/', root).href });
  // Current pinned Pyodide includes sqlite3 in the core standard library.
  python.FS.mkdirTree('/aiko-save');
  python.FS.mount(python.FS.filesystems.IDBFS, {}, '/aiko-save');
  await sync(true);
  const code = await fetch(new URL('python/aiko.zip', root));
  if (!code.ok) throw new Error('Python-Paket fehlt.');
  python.FS.mkdirTree('/app');
  python.unpackArchive(await code.arrayBuffer(), 'zip', { extractDir: '/app' });
  const wheels: string[] = await (
    await fetch(new URL('python/wheels.json', root))
  ).json();
  const site = python.runPython('import site; site.getsitepackages()[0]') as string;
  for (const wheel of wheels) {
    const response = await fetch(new URL(`python/${wheel}`, root));
    if (!response.ok) throw new Error(`Python-Abhängigkeit fehlt: ${wheel}`);
    python.unpackArchive(await response.arrayBuffer(), 'zip', { extractDir: site });
  }
  python.runPython(
    "import sys; sys.path.insert(0, '/app'); from aiko_pet.browser.bootstrap import create_browser_session; _aiko = create_browser_session('/aiko-save/state.sqlite3')",
  );
  session = python.globals.get('_aiko') as typeof session;
}
let queue = Promise.resolve();
self.onmessage = (event) => {
  const message = event.data as {
    requestId: number;
    name: string;
    args?: Record<string, unknown>;
    root?: string;
  };
  queue = queue.then(async () => {
    try {
      if (message.name === 'initialize') await initialize(message.root!);
      if (!session) throw new Error('Aiko ist noch nicht bereit.');
      const reply = JSON.parse(
        session.dispatch_json(
          JSON.stringify({
            ...message,
            protocol: roomProtocol,
            name: message.name === 'initialize' ? 'snapshot' : message.name,
          }),
        ),
      ) as Record<string, unknown>;
      // A successful command is durable only after IDBFS acknowledges the flush.
      // No later command enters Python while an asynchronous flush is pending.
      dirty = true;
      await sync(false);
      dirty = false;
      self.postMessage({ ...reply, saved: true });
    } catch (error) {
      self.postMessage({
        protocol: roomProtocol,
        requestId: message.requestId,
        ok: false,
        saved: !dirty,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  });
};
