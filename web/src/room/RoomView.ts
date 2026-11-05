import { Application, Assets, Container, Sprite, Texture, Graphics } from 'pixi.js';
import type { FederatedPointerEvent } from 'pixi.js';
import { Viewport } from 'pixi-viewport';
import type { RoomSnapshot } from '../bridge/RoomClient';
import { AikoView } from './AikoView';
import type { Clip } from './AikoView';
import type { PetScreenBounds } from './AikoView';
import { RoomCamera } from './RoomCamera';
import { RoomMotion } from './RoomMotion';
import { paintRoomFloor } from './RoomFloor';
import { depthScale, feetY, projectX, unproject, wrap } from './RoomProjection';

export interface AssetManifest {
  characterHeight: number;
  foregroundDepth: [number, number];
  ui: {
    icons: Record<string, Record<string, string>>;
    surfaces: Record<string, string>;
  };
  clips: Record<string, Clip>;
  items: Record<
    string,
    {
      file: string;
      label: string;
      pivot: [number, number];
      states?: Record<string, string>;
      size?: number;
      dimensions: [number, number];
    }
  >;
  room: Record<string, string>;
}
type WorldItem = RoomSnapshot['objects'][number];
export interface DragPlacement {
  x: number;
  depth: number;
  height: number;
  inside: boolean;
  offer: boolean;
  face_x: number;
  face_y: number;
}
const cutouts: Record<string, { crop: number[]; width: number; x: number; y: number }> =
  {
    bed: { crop: [56, 126, 1659, 665], width: 680, x: 4780, y: 820 },
    desk: { crop: [44, 178, 1265, 821], width: 386, x: 4240, y: 820 },
    shelf: { crop: [124, 122, 1121, 923], width: 270, x: 3920, y: 540 },
    plant: { crop: [94, 84, 943, 1245], width: 204, x: 3750, y: 810 },
    table: { crop: [216, 138, 1741, 489], width: 527, x: 2450, y: 840 },
    fridge: { crop: [140, 130, 760, 1350], width: 244, x: 1425, y: 802 },
    door: { crop: [163, 107, 698, 1319], width: 255, x: 315, y: 784 },
    kitchenUnit: {
      crop: [115, 85, 964, 1183],
      width: (475 * 964) / 1183,
      x: 930,
      y: 820,
    },
  };

export class RoomView {
  readonly app = new Application();
  camera!: RoomCamera;
  private world = new Container();
  private aiko!: AikoView;
  private shadow = new Graphics()
    .ellipse(0, -3, 60, 8)
    .fill({ color: 0x1b3a5d, alpha: 0.2 });
  private viewport!: Viewport;
  private objects = new Map<
    string,
    { sprite: Sprite; item: WorldItem; motion: RoomMotion }
  >();
  private snapshot?: RoomSnapshot;
  private motion = new RoomMotion();
  private disposed = false;
  private followers = new Set<(bounds: PetScreenBounds) => void>();
  draggingInstance?: string;
  dragging = false;
  dragVisual?: { x: number; y: number };
  private petTapBlockedUntil = 0;
  onObjectDown: (item: WorldItem, event: FederatedPointerEvent) => void = () => {};
  onPetTap: () => void = () => {};
  private resizeObserver?: ResizeObserver;

  constructor(
    private host: HTMLElement,
    readonly root: string,
    readonly assets: AssetManifest,
  ) {}

  async initialize(): Promise<void> {
    await this.app.init({
      resizeTo: this.host,
      background: '#f7f2f3',
      antialias: true,
      resolution: Math.min(2, devicePixelRatio),
      autoDensity: true,
      preference: 'webgl',
    });
    this.host.append(this.app.canvas);
    this.viewport = new Viewport({
      screenWidth: this.host.clientWidth,
      screenHeight: this.host.clientHeight,
      worldWidth: 15300,
      worldHeight: 900,
      events: this.app.renderer.events,
    });
    this.app.stage.addChild(this.viewport);
    this.camera = new RoomCamera(this.viewport);
    this.world.sortableChildren = true;
    this.viewport.addChild(this.world);
    const imageEntries = await Promise.all(
      Object.entries(this.assets.room).map(async ([id, file]) => {
        const image = new Image();
        image.src = new URL(`room/${file}`, this.root).href;
        await image.decode();
        return [id, image] as const;
      }),
    );
    const images = Object.fromEntries(imageEntries);
    const background = document.createElement('canvas');
    background.width = 5100;
    background.height = 900;
    const ctx = background.getContext('2d')!;
    ctx.drawImage(images.kitchen!, 0, 0, 1800, 900);
    ctx.drawImage(images.living!, 1800, 0, 1800, 900);
    const wall = images.kitchen!;
    ctx.drawImage(
      wall,
      0,
      0,
      (1500 * wall.height) / 900,
      wall.height,
      3600,
      0,
      1500,
      900,
    );
    // The v16 reference uses narrow architectural pillars at every panel join,
    // including both ends of the 360-degree loop. Keep art coordinates intact.
    paintRoomFloor(ctx, wall);
    for (const x of [0, 1800, 3600, 5100]) {
      ctx.fillStyle = '#e7e3f0';
      ctx.strokeStyle = '#a1abc6';
      ctx.lineWidth = 2;
      ctx.fillRect(x - 18, 53, 36, 749);
      ctx.strokeRect(x - 18, 53, 36, 749);
    }
    const texture = Texture.from(background);
    const furnitureTextures = new Map<string, Texture>();
    for (const [name, definition] of Object.entries(cutouts)) {
      const source = images[name]!;
      const [x, y, w, h] = definition.crop as [number, number, number, number];
      const canvas = document.createElement('canvas');
      canvas.width = w;
      canvas.height = h;
      canvas.getContext('2d')!.drawImage(source, x, y, w, h, 0, 0, w, h);
      furnitureTextures.set(name, Texture.from(canvas));
    }
    for (const offset of [-5100, 0, 5100]) {
      const tile = new Sprite(texture);
      tile.x = offset;
      tile.zIndex = -10000;
      this.world.addChild(tile);
      for (const [name, definition] of Object.entries(cutouts)) {
        const [x, y, w, h] = definition.crop as [number, number, number, number];
        const furniture = new Sprite(furnitureTextures.get(name)!);
        furniture.anchor.set(0.5, 1);
        furniture.width = definition.width;
        furniture.height = (h / w) * definition.width;
        furniture.position.set(offset + definition.x, definition.y);
        furniture.zIndex = -1000;
        this.world.addChild(furniture);
      }
    }
    this.aiko = new AikoView(this.root, this.assets.clips, this.assets.items);
    this.aiko.on('pointertap', () => {
      if (performance.now() > this.petTapBlockedUntil) this.onPetTap();
    });
    this.world.addChild(this.shadow, this.aiko);
    await this.aiko.show('idle');
    await this.aiko.warmWalking();
    this.resizeObserver = new ResizeObserver(() =>
      this.camera.resize(this.host.clientWidth, this.host.clientHeight),
    );
    this.resizeObserver.observe(this.host);
    this.camera.resize(this.host.clientWidth, this.host.clientHeight);
    this.camera.lookAt(600);
    this.app.ticker.add(() => this.draw());
  }

  async update(snapshot: RoomSnapshot): Promise<void> {
    let contact: { x: number; y: number } | undefined;
    if (snapshot.held_item && snapshot.held_item !== this.snapshot?.held_item) {
      if (this.dragVisual) {
        const box = this.app.canvas.getBoundingClientRect();
        contact = this.aiko.toLocal({
          x: this.dragVisual.x - box.left,
          y: this.dragVisual.y - box.top,
        });
      } else {
        const incoming = snapshot.objects.find((item) => item.state === 'pet_held');
        const previous = incoming && this.objects.get(incoming.instance_id);
        if (previous) {
          const asset = this.assets.items[incoming!.definition_id]!;
          contact = this.aiko.toLocal(
            this.world.toGlobal({
              x:
                previous.sprite.x +
                (asset.pivot[0] - asset.dimensions[0] / 2) * previous.sprite.scale.x,
              y:
                previous.sprite.y -
                (asset.dimensions[1] - asset.pivot[1]) * previous.sprite.scale.y,
            }),
          );
        }
      }
    }
    this.snapshot = snapshot;
    this.motion.receive(snapshot.room.pet);
    void this.aiko.show(
      snapshot.animation,
      snapshot.animation_id,
      snapshot.animation_timings,
      snapshot.animation_hold_frame,
    );
    void this.aiko.hold(snapshot.held_item ?? null, snapshot.held_pose, contact);
    const live = new Set(
      snapshot.objects
        .filter((item) => !['consumed', 'removed'].includes(item.state))
        .map((item) => item.instance_id),
    );
    for (const [id, current] of this.objects)
      if (!live.has(id)) {
        current.sprite.destroy();
        this.objects.delete(id);
      }
    for (const item of snapshot.objects) {
      if (!live.has(item.instance_id) || this.objects.has(item.instance_id)) {
        const known = this.objects.get(item.instance_id);
        if (known) {
          if (known.item.state !== item.state) known.motion = new RoomMotion();
          known.item = item;
          if (item.position)
            known.motion.receive({
              ...item.position,
              depth: new Map(snapshot.room.object_depths).get(item.instance_id) ?? 0.9,
            });
        }
        continue;
      }
      const asset = this.assets.items[item.definition_id];
      if (!asset) continue;
      const texture = await Assets.load<Texture>(new URL(asset.file, this.root).href);
      if (this.disposed) return;
      if (this.objects.has(item.instance_id)) continue;
      if (
        !this.snapshot?.objects.some(
          (current) =>
            current.instance_id === item.instance_id &&
            !['consumed', 'removed'].includes(current.state),
        )
      )
        continue;
      const sprite = new Sprite(texture);
      sprite.anchor.set(0.5, 1);
      sprite.eventMode = 'static';
      sprite.cursor = 'grab';
      sprite.on('pointerdown', (event) => {
        const current = this.objects.get(item.instance_id);
        if (current) this.onObjectDown(current.item, event);
      });
      this.world.addChild(sprite);
      const motion = new RoomMotion();
      if (item.position)
        motion.receive({
          ...item.position,
          depth: new Map(snapshot.room.object_depths).get(item.instance_id) ?? 0.9,
        });
      this.objects.set(item.instance_id, { sprite, item, motion });
    }
    this.draw();
  }

  private draw(): void {
    const snapshot = this.snapshot;
    if (!snapshot) return;
    const center = this.viewport.center.x;
    const point = this.motion.position() ?? snapshot.room.pet;
    this.aiko.position.set(projectX(point.x, point.depth, center), feetY(point.depth));
    const settings = snapshot.catalog.settings as Record<string, unknown>;
    const size = settings.scale === 2 ? 1.25 : 1;
    this.aiko.scale.set(
      (400 / this.assets.characterHeight) * depthScale(point.depth) * size,
    );
    this.aiko.zIndex = feetY(point.depth);
    this.aiko.renderHeld();
    this.shadow.position.copyFrom(this.aiko.position);
    this.shadow.scale.set(depthScale(point.depth) * size);
    this.shadow.zIndex = this.aiko.zIndex - 0.1;
    for (const follow of this.followers) follow(this.aiko.screenBounds());
    const depths = new Map(snapshot.room.object_depths);
    for (const { sprite, item, motion } of this.objects.values()) {
      const position = item.position;
      sprite.visible =
        position !== null &&
        item.state !== 'pet_held' &&
        !(this.dragging && item.state === 'user_held') &&
        item.instance_id !== this.draggingInstance;
      if (!position) continue;
      const display = motion.position() ?? {
        ...position,
        depth: depths.get(item.instance_id) ?? 0.9,
      };
      const depth = display.depth;
      sprite.position.set(
        projectX(display.x, depth, center),
        feetY(depth) - (display.height ?? position.height),
      );
      sprite.scale.set((depthScale(depth) * 400) / this.assets.characterHeight);
      sprite.zIndex = feetY(depth);
    }
  }

  pointAt(clientX: number, clientY: number): { x: number; depth: number } {
    const box = this.app.canvas.getBoundingClientRect();
    const world = this.viewport.toWorld(clientX - box.left, clientY - box.top);
    return unproject(world.x, world.y, this.viewport.center.x);
  }
  petContains(clientX: number, clientY: number): boolean {
    const box = this.app.canvas.getBoundingClientRect();
    const bounds = this.aiko.screenBounds();
    const x = clientX - box.left,
      y = clientY - box.top;
    return (
      x >= bounds.x &&
      x <= bounds.x + bounds.width &&
      y >= bounds.y &&
      y <= bounds.y + bounds.height
    );
  }
  suppressPetTap(): void {
    this.petTapBlockedUntil = performance.now() + 350;
  }
  portionSize(definition: string, x: number, y: number): [number, number] {
    return this.portionSizeAt(
      definition,
      this.floorPoint(x, y)?.depth ?? this.petPosition?.depth ?? 0.9,
    );
  }
  portionSizeAt(definition: string, depth: number): [number, number] {
    const dimensions = this.assets.items[definition]?.dimensions ?? [72, 72];
    const factor =
      this.viewport.scale.x * (400 / this.assets.characterHeight) * depthScale(depth);
    return [dimensions[0]! * factor, dimensions[1]! * factor];
  }
  objectDepth(instance: string): number {
    return new Map(this.snapshot?.room.object_depths).get(instance) ?? 0.9;
  }
  dragPoint(
    clientX: number,
    clientY: number,
    depth: number,
    definition: string,
  ): DragPlacement {
    const box = this.app.canvas.getBoundingClientRect();
    const world = this.viewport.toWorld(clientX - box.left, clientY - box.top);
    const asset = this.assets.items[definition]!;
    const scale = (depthScale(depth) * 400) / this.assets.characterHeight;
    const support = (asset.dimensions[1] - asset.pivot[1]) * scale;
    const groundY = world.y + support;
    if (this.petContains(clientX, clientY) && this.petPosition)
      depth = this.petPosition.depth;
    else if (groundY >= feetY(0.2) && groundY <= feetY(1.55))
      depth = unproject(world.x, groundY, this.viewport.center.x).depth;
    depth = Math.max(
      this.assets.foregroundDepth[0],
      Math.min(this.assets.foregroundDepth[1], depth),
    );
    const point = unproject(world.x, feetY(depth), this.viewport.center.x);
    const height = Math.max(0, Math.min(900, feetY(depth) - groundY));
    const pet = this.aiko.screenBounds();
    const width = pet.scale * 192;
    const inside =
      clientX >= box.left &&
      clientX <= box.right &&
      clientY >= box.top &&
      clientY <= box.bottom;
    return {
      ...point,
      depth,
      height,
      inside,
      offer: inside && this.petContains(clientX, clientY),
      face_x: (clientX - box.left - pet.originX - pet.scale * 96) / width,
      face_y: (clientY - box.top - pet.originY - pet.scale * 100) / width,
    };
  }
  followPet(callback: (bounds: PetScreenBounds) => void): () => void {
    this.followers.add(callback);
    return () => this.followers.delete(callback);
  }
  frameForGame(): void {
    this.camera.setGame(true);
    const point = this.petPosition;
    if (!point) return;
    const desired = this.camera.portraitGame
      ? this.host.clientWidth * 0.5
      : Math.min(
          this.host.clientWidth * 0.35,
          Math.max(160, this.host.clientWidth - 560) * 0.7,
        );
    const offset =
      (((this.host.clientWidth / 2 - desired) / this.viewport.scale.x) *
        depthScale(0.9)) /
      depthScale(point.depth);
    this.camera.lookAt(point.x + offset);
  }
  floorPoint(
    clientX: number,
    clientY: number,
  ): { x: number; depth: number } | undefined {
    const box = this.app.canvas.getBoundingClientRect();
    if (
      clientX < box.left ||
      clientX > box.right ||
      clientY < box.top ||
      clientY > box.bottom
    )
      return;
    const world = this.viewport.toWorld(clientX - box.left, clientY - box.top);
    if (world.y < feetY(0.2) || world.y > feetY(1.55)) return;
    const point = this.pointAt(clientX, clientY);
    return {
      ...point,
      depth: Math.max(
        this.assets.foregroundDepth[0],
        Math.min(this.assets.foregroundDepth[1], point.depth),
      ),
    };
  }
  callPoint(): { x: number; depth: number } {
    return { x: wrap(this.viewport.center.x), depth: 1.1 };
  }
  get petPosition(): { x: number; depth: number } | undefined {
    return this.snapshot?.room.pet;
  }
  destroy(): void {
    this.disposed = true;
    this.followers.clear();
    this.resizeObserver?.disconnect();
    this.app.destroy(true, { children: true });
  }
}
