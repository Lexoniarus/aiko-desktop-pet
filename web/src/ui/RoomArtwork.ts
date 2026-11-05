import type { AssetManifest } from '../room/RoomView';
import { element } from './dom';

/** Resolve the same catalogued UI and game artwork as the desktop frontend. */
export class RoomArtwork {
  constructor(
    readonly root: string,
    private ui: AssetManifest['ui'],
  ) {}
  file(path: string): string {
    return new URL(`assets/${path}`, this.root).href;
  }
  icon(key: string, size = 96): string {
    const filename = this.ui.icons[key]?.[String(size)];
    if (!filename) throw new Error(`Fehlendes UI-Bild: ${key}/${size}`);
    return this.file(`ui/${filename}`);
  }
  surface(key: string): string {
    return this.file(`ui/${this.ui.surfaces[key]}`);
  }
  game(name: string): string {
    return this.file(`game_frontends/${name}.png`);
  }
  image(src: string, alt = '', className = ''): HTMLImageElement {
    const image = element('img', className);
    if (src) image.src = src;
    image.alt = alt;
    image.draggable = false;
    return image;
  }
  apply(host: HTMLElement): void {
    host.style.setProperty(
      '--bubble-art',
      `url("${this.surface('panel_surface.game_bubble')}")`,
    );
    host.style.setProperty(
      '--panel-art',
      `url("${this.surface('panel_surface.panel')}")`,
    );
    for (const state of ['normal', 'hover', 'pressed', 'disabled'])
      host.style.setProperty(
        `--button-${state}`,
        `url("${this.surface(`button_${state}.regular`)}")`,
      );
  }
}
