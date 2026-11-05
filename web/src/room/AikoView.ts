import { AnimatedSprite, Assets, Container, Texture, Sprite } from 'pixi.js';

export interface Clip {
  frames: Array<{
    file: string;
    duration: number;
    foodAnchor: [number, number] | null;
    foreground: string | null;
  }>;
  order: number[];
  loop: boolean;
  anchor: [number, number];
  duration: number;
}
export class AikoView extends Container {
  private sprite = new AnimatedSprite([Texture.EMPTY]);
  private clipName = '';
  private generation = 0;
  private actionId = -1;
  private held = new Sprite(Texture.EMPTY);
  private foreground = new Sprite(Texture.EMPTY);
  private foregroundFrames = new Map<string, Array<Texture | null>>();
  private heldKey = '';
  private loaded = new Map<string, Array<{ texture: Texture; time: number }>>();
  constructor(
    private root: string,
    private clips: Record<string, Clip>,
    private items: Record<
      string,
      { file: string; pivot: [number, number]; states?: Record<string, string> }
    >,
  ) {
    super();
    this.addChild(this.sprite, this.held, this.foreground);
    this.held.visible = false;
    this.foreground.visible = false;
    this.sprite.onFrameChange = () => this.placeHeld();
    this.eventMode = 'static';
    this.cursor = 'pointer';
  }
  async show(name: string, actionId = 0): Promise<void> {
    if (!(name in this.clips)) name = 'idle';
    if (name === this.clipName && actionId === this.actionId) return;
    this.actionId = actionId;
    this.clipName = name;
    const generation = ++this.generation;
    const clip = this.clips[name]!;
    let frames = this.loaded.get(name);
    if (!frames) {
      const textures = await Promise.all(
        clip.frames.map((frame) =>
          Assets.load<Texture>(new URL(frame.file, this.root).href),
        ),
      );
      frames = (
        clip.order.length ? clip.order : clip.frames.map((_frame, index) => index)
      ).map((index) => ({
        texture: textures[index]!,
        time: clip.frames[index]!.duration,
      }));
      this.loaded.set(name, frames);
      this.foregroundFrames.set(
        name,
        await Promise.all(
          clip.frames.map((frame) =>
            frame.foreground
              ? Assets.load<Texture>(new URL(frame.foreground, this.root).href)
              : Promise.resolve(null),
          ),
        ),
      );
    }
    if (generation !== this.generation) return;
    this.sprite.textures = frames;
    this.sprite.anchor.set(clip.anchor[0] / 192, clip.anchor[1] / 208);
    this.sprite.loop = clip.loop;
    this.sprite.gotoAndPlay(0);
    this.placeHeld();
  }
  async hold(item: string | null, pose = 'closed_world'): Promise<void> {
    const definition = item ? this.items[item] : undefined;
    const file = definition?.states?.[pose] ?? definition?.file ?? '';
    if (file === this.heldKey) return;
    this.heldKey = file;
    if (!definition) {
      this.held.visible = false;
      return;
    }
    const texture = await Assets.load<Texture>(new URL(file, this.root).href);
    if (file !== this.heldKey) return;
    this.held.texture = texture;
    this.held.anchor.set(
      definition.pivot[0] / texture.width,
      definition.pivot[1] / texture.height,
    );
    this.placeHeld();
  }
  private placeHeld(): void {
    const clip = this.clips[this.clipName];
    if (!clip) return;
    const index = clip.order[this.sprite.currentFrame] ?? this.sprite.currentFrame;
    const anchor = clip.frames[index]?.foodAnchor;
    this.held.visible = !!anchor && !!this.heldKey;
    const foreground = this.foregroundFrames.get(this.clipName)?.[index];
    this.foreground.visible = this.held.visible && !!foreground;
    if (foreground) {
      this.foreground.texture = foreground;
      this.foreground.anchor.copyFrom(this.sprite.anchor);
      this.foreground.width = this.sprite.texture.width;
      this.foreground.height = this.sprite.texture.height;
    }
    if (anchor)
      this.held.position.set(
        (anchor[0] - clip.anchor[0]) * 2,
        (anchor[1] - clip.anchor[1]) * 2,
      );
  }
}
