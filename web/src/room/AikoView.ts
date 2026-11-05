import { AnimatedSprite, Assets, Container, Texture } from 'pixi.js';

export interface Clip {
  frames: Array<{ file: string; duration: number; foodAnchor: [number, number] | null; foreground: string | null }>;
  order: number[]; loop: boolean; anchor: [number, number]; duration: number;
}
export class AikoView extends Container {
  private sprite = new AnimatedSprite([Texture.EMPTY]);
  private name = '';
  private generation = 0;
  private loaded = new Map<string, Array<{ texture: Texture; time: number }>>();
  constructor(private root: string, private clips: Record<string, Clip>) {
    super(); this.addChild(this.sprite); this.eventMode = 'static'; this.cursor = 'pointer';
  }
  async show(name: string): Promise<void> {
    if (!(name in this.clips)) name = 'idle';
    if (name === this.name) return;
    this.name = name;
    const generation = ++this.generation;
    const clip = this.clips[name]!;
    let frames = this.loaded.get(name);
    if (!frames) {
      const textures = await Promise.all(clip.frames.map(frame => Assets.load<Texture>(new URL(frame.file, this.root).href)));
      frames = (clip.order.length ? clip.order : clip.frames.map((_frame, index) => index))
        .map(index => ({ texture: textures[index]!, time: clip.frames[index]!.duration }));
      this.loaded.set(name, frames);
    }
    if (generation !== this.generation) return;
    this.sprite.textures = frames;
    this.sprite.anchor.set(clip.anchor[0] / 192, clip.anchor[1] / 208);
    this.sprite.loop = clip.loop;
    this.sprite.gotoAndPlay(0);
  }
}
