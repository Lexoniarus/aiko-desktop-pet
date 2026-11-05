import { AnimatedSprite, Assets, Container, Texture, Sprite, Rectangle } from 'pixi.js';

export interface Clip {
  frames: Array<{
    file: string;
    duration: number;
    foodAnchor: [number, number] | null;
    foreground: string | null;
    bounds: [number, number, number, number];
  }>;
  order: number[];
  loop: boolean;
  anchor: [number, number];
  duration: number;
  family?: string;
}
export interface PetScreenBounds {
  x: number;
  y: number;
  width: number;
  height: number;
  originX: number;
  originY: number;
  scale: number;
}
export class AikoView extends Container {
  private sprite = new AnimatedSprite([Texture.EMPTY]);
  private clipName = '';
  private generation = 0;
  private actionId = -1;
  private holdFrame: number | null = null;
  private held = new Sprite(Texture.EMPTY);
  private foreground = new Sprite(Texture.EMPTY);
  private foregroundFrames = new Map<string, Array<Texture | null>>();
  private heldKey = '';
  private heldItem = '';
  private contact?: { x: number; y: number; at: number };
  private chipHands?: Texture[];
  private disposed = false;
  private frameBounds = new Rectangle();
  private loaded = new Map<string, Array<{ texture: Texture; time: number }>>();
  constructor(
    private root: string,
    private clips: Record<string, Clip>,
    private items: Record<
      string,
      {
        file: string;
        pivot: [number, number];
        states?: Record<string, string>;
        size?: number;
      }
    >,
  ) {
    super();
    this.addChild(this.sprite, this.held, this.foreground);
    this.held.visible = false;
    this.foreground.visible = false;
    this.sprite.onFrameChange = () => {
      this.placeHeld();
      this.updateBounds();
    };
    this.eventMode = 'static';
    this.cursor = 'pointer';
  }
  async show(
    name: string,
    actionId = 0,
    timings?: number[] | null,
    holdFrame?: number | null,
  ): Promise<void> {
    if (!(name in this.clips)) name = 'idle';
    const fixed = holdFrame ?? null;
    if (
      name === this.clipName &&
      (actionId === this.actionId || this.clips[name]!.loop) &&
      fixed === this.holdFrame
    )
      return;
    const previous = this.clips[this.clipName];
    const phase =
      previous?.family && previous.family === this.clips[name]?.family
        ? this.sprite.currentFrame
        : 0;
    this.actionId = actionId;
    this.holdFrame = fixed;
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
    if (this.disposed || generation !== this.generation) return;
    this.sprite.textures = timings
      ? frames.map((frame, index) => ({
          texture: frame.texture,
          time: timings[index] ?? frame.time,
        }))
      : frames;
    this.sprite.anchor.set(clip.anchor[0] / 192, clip.anchor[1] / 208);
    this.sprite.loop = clip.loop;
    if (holdFrame !== null && holdFrame !== undefined)
      this.sprite.gotoAndStop(
        Math.max(0, clip.order.length ? clip.order.indexOf(holdFrame) : holdFrame),
      );
    else this.sprite.gotoAndPlay(Math.min(phase, frames.length - 1));
    this.placeHeld();
    this.updateBounds();
  }
  async warmWalking(): Promise<void> {
    const names = [
      'body-step-right-04',
      'body-step-left-12',
      'body-look-right',
      'body-look-left',
    ];
    await Promise.all(
      names.flatMap(
        (name) =>
          this.clips[name]?.frames.map((frame) =>
            Assets.load<Texture>(new URL(frame.file, this.root).href),
          ) ?? [],
      ),
    );
  }
  async hold(
    item: string | null,
    pose = 'closed_world',
    contact?: { x: number; y: number },
  ): Promise<void> {
    const definition = item ? this.items[item] : undefined;
    const file = definition?.states?.[pose] ?? definition?.file ?? '';
    if (file === this.heldKey) return;
    this.heldKey = file;
    this.heldItem = item ?? '';
    this.contact = contact ? { ...contact, at: performance.now() } : undefined;
    if (!definition) {
      this.held.visible = false;
      return;
    }
    const texture = await Assets.load<Texture>(new URL(file, this.root).href);
    if (this.disposed || file !== this.heldKey) return;
    this.held.texture = texture;
    this.held.scale.set(definition.size ? definition.size / texture.width : 1);
    this.held.anchor.set(
      definition.pivot[0] / texture.width,
      definition.pivot[1] / texture.height,
    );
    this.placeHeld();
    if (item === 'c4-red' && !this.chipHands) {
      const hands = await Promise.all(
        [3, 4, 5].map((index) =>
          Assets.load<Texture>(
            new URL(`assets/game_frontends/c4-hands/0${index}.png`, this.root).href,
          ),
        ),
      );
      if (!this.disposed) {
        this.chipHands = hands;
        this.placeHeld();
      }
    }
  }
  renderHeld(): void {
    this.placeHeld();
  }
  private updateBounds(): void {
    const clip = this.clips[this.clipName];
    if (!clip) return;
    const index = clip.order[this.sprite.currentFrame] ?? this.sprite.currentFrame;
    const bounds = clip.frames[index]?.bounds;
    if (!bounds) return;
    this.frameBounds = new Rectangle(
      bounds[0] - clip.anchor[0] * 2,
      bounds[1] - clip.anchor[1] * 2,
      bounds[2] - bounds[0],
      bounds[3] - bounds[1],
    );
    this.hitArea = this.frameBounds;
  }
  screenBounds(): PetScreenBounds {
    const top = this.toGlobal({ x: this.frameBounds.x, y: this.frameBounds.y });
    const bottom = this.toGlobal({
      x: this.frameBounds.right,
      y: this.frameBounds.bottom,
    });
    const clip = this.clips[this.clipName]!;
    const origin = this.toGlobal({ x: -clip.anchor[0] * 2, y: -clip.anchor[1] * 2 });
    const zero = this.toGlobal({ x: 0, y: 0 }),
      unit = this.toGlobal({ x: 2, y: 0 });
    return {
      x: top.x,
      y: top.y,
      width: bottom.x - top.x,
      height: bottom.y - top.y,
      originX: origin.x,
      originY: origin.y,
      scale: unit.x - zero.x,
    };
  }
  override destroy(): void {
    this.disposed = true;
    this.generation++;
    super.destroy({ children: true });
  }
  private placeHeld(): void {
    const clip = this.clips[this.clipName];
    if (!clip) return;
    const index = clip.order[this.sprite.currentFrame] ?? this.sprite.currentFrame;
    const chip = this.heldItem === 'c4-red' && this.clipName === 'pick_up';
    const chipAnchors: Record<number, [number, number]> = {
      3: [96, 181],
      4: [96, 171],
      5: [96, 143],
    };
    const anchor = chip ? chipAnchors[index] : clip.frames[index]?.foodAnchor;
    this.held.visible = !!anchor && !!this.heldKey;
    // Desktop FoodOverlay raises ordinary food/books over the character.
    // Only the game's chip pickup deliberately uses a foreground hand mask.
    const foreground = chip ? this.chipHands?.[index - 3] : undefined;
    this.foreground.visible = this.held.visible && !!foreground;
    if (foreground) {
      this.foreground.texture = foreground;
      this.foreground.anchor.copyFrom(this.sprite.anchor);
      this.foreground.width = this.sprite.texture.width;
      this.foreground.height = this.sprite.texture.height;
    }
    if (anchor) {
      let x = (anchor[0] - clip.anchor[0]) * 2;
      let y = (anchor[1] - clip.anchor[1]) * 2;
      if (this.contact && this.clipName !== 'put_down') {
        const blend = Math.min(1, (performance.now() - this.contact.at) / 130);
        x = this.contact.x * (1 - blend) + x * blend;
        y = this.contact.y * (1 - blend) + y * blend;
      }
      this.held.position.set(x, y);
    }
  }
}
