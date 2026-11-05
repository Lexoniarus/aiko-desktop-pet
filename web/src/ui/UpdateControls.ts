import type { RoomUpdates } from '../bridge/RoomUpdates';
import { button, element } from './dom';

export class UpdateControls {
  readonly element = element('section', 'update-controls');
  constructor(updates: RoomUpdates) {
    const version = element('p');
    const status = element('p');
    status.setAttribute('role', 'status');
    const check = button('Nach Updates suchen', () => {
      void updates.check();
    });
    const restart = button('Jetzt neu starten', () => {
      void updates.apply();
    });
    this.element.append(
      element('h3', '', 'App-Version und Updates'),
      version,
      status,
      check,
      restart,
    );
    updates.subscribe((state) => {
      version.textContent = `Installiert: ${state.installedVersion}${state.availableVersion ? ` · Update: ${state.availableVersion}` : ''}`;
      status.textContent = state.message;
      check.disabled = ['checking', 'downloading', 'applying'].includes(state.phase);
      restart.hidden = state.phase !== 'ready';
      restart.disabled = !state.canRestart;
      restart.title = state.canRestart
        ? 'Spielstand sichern und Update öffnen'
        : 'Erst das laufende Spiel beenden';
    });
  }
}
