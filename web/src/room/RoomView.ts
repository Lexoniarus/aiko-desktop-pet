import { Application, Assets, Container, Sprite, Texture, Graphics } from 'pixi.js';
import type { FederatedPointerEvent } from 'pixi.js';
import { Viewport } from 'pixi-viewport';
import type { RoomSnapshot } from '../bridge/RoomClient';
import { AikoView } from './AikoView';
import type { Clip } from './AikoView';
import type { PetScreenBounds } from './AikoView';
import { RoomCamera } from './RoomCamera';
import { RoomMotion } from './RoomMotion';
import { RoomScene } from './RoomScene';
import { RoomPicking } from './RoomPicking';
import type { RoomLayout, RoomPoint } from './RoomLayout';
import type { RoomItemAsset } from './RoomAssets';
import { furnitureFrame } from './RoomPresentation';
import { objectGroundOrder } from './RoomDepthOrder';
import { tableGameFrame } from '../games/ConnectFourGeometry';

export interface AssetManifest {
  packageVersion: string;
  buildTimestamp: number;
  characterHeight: number;
  layout: RoomLayout;
  ui: {
    icons: Record<string, Record<string, string>>;
    surfaces: Record<string, string>;
  };
  clips: Record<string, Clip>;
  items: Record<string, RoomItemAsset>;
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
  private scene!: RoomScene;
  private picking!: RoomPicking;
  private disposed = false;
  private followers = new Set<(bounds: PetScreenBounds) => void>();
  draggingInstance?: string;
  dragging = false;
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
    this.camera = new RoomCamera(this.app.canvas, this.assets.layout);
    this.picking = new RoomPicking(this.camera);
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
    this.scene = new RoomScene(this.world, this.assets.layout, images);
    this.aiko = new AikoView(this.root, this.assets.clips, this.assets.items);
    this.aiko.on('pointertap', () => {
      if (performance.now() > this.petTapBlockedUntil && !this.camera.blocksTap)
        this.onPetTap();
    });
    this.world.addChild(this.shadow, this.aiko);
    await this.aiko.show('idle');
    await this.aiko.warmWalking();
    this.resizeObserver = new ResizeObserver(() =>
      this.camera.resize(this.host.clientWidth, this.host.clientHeight),
    );
    this.resizeObserver.observe(this.host);
    this.camera.resize(this.host.clientWidth, this.host.clientHeight);
    this.camera.lookAt({ x: 400, depth: 100 });
    this.app.ticker.add(() => this.draw());
  }

  async update(snapshot: RoomSnapshot): Promise<void> {
    this.snapshot = snapshot;
    this.motion.receive(
      snapshot.room.pet,
      performance.now(),
      snapshot.motion?.travelled,
    );
    void this.aiko.hold(snapshot.held_item ?? null, snapshot.held_pose);
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
              depth: new Map(snapshot.room.object_depths).get(item.instance_id) ?? 300,
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
      sprite.anchor.set(
        asset.pivot[0] / texture.width,
        asset.pivot[1] / texture.height,
      );
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
          depth: new Map(snapshot.room.object_depths).get(item.instance_id) ?? 300,
        });
      this.objects.set(item.instance_id, { sprite, item, motion });
    }
    this.draw();
  }

  private draw(): void {
    const snapshot = this.snapshot;
    if (!snapshot) return;
    const point = this.motion.position() ?? snapshot.room.pet;
    this.camera.tick(point);
    this.scene.update(this.camera);
    void this.aiko.showFromCamera(
      snapshot.animation,
      snapshot.heading ?? 0,
      Math.atan2(
        point.x - this.assets.layout.width / 2,
        this.assets.layout.depth / 2 - point.depth,
      ),
      snapshot.moving,
      snapshot.animation_id,
      snapshot.animation_timings,
      snapshot.animation_hold_frame,
    );
    const projected = this.camera.projection.projectPoint(point);
    this.aiko.visible = projected.depth > 1;
    this.aiko.position.set(projected.x, projected.y);
    this.aiko.scale.set(
      (this.assets.layout.pet_height / this.assets.characterHeight) * projected.scale,
    );
    this.aiko.zIndex = projected.groundY;
    this.aiko.renderHeld(
      snapshot.game?.id === 'connect_four' ? this.tableGameFrame()?.chip : undefined,
    );
    this.shadow.position.copyFrom(this.aiko.position);
    this.shadow.visible = this.aiko.visible;
    this.shadow.scale.set(projected.scale / 4);
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
        depth: depths.get(item.instance_id) ?? 300,
      };
      const p = this.camera.projection.projectPoint(
        display,
        display.height ?? position.height,
      );
      sprite.visible &&= p.depth > 1;
      sprite.position.set(p.x, p.y);
      sprite.scale.set(
        (this.assets.layout.pet_height / this.assets.characterHeight) *
          p.scale *
          (this.assets.items[item.definition_id]?.worldZoom ?? 1),
      );
      sprite.zIndex = objectGroundOrder(
        this.assets.layout,
        point,
        display,
        projected.groundY,
        p.groundY,
      );
    }
  }

  pointAt(clientX: number, clientY: number): RoomPoint {
    return (
      this.floorPoint(clientX, clientY) ?? this.petPosition ?? { x: 400, depth: 100 }
    );
  }
  petContains(clientX: number, clientY: number): boolean {
    const box = this.app.canvas.getBoundingClientRect();
    const bounds = this.aiko.screenBounds();
    const x = clientX - box.left,
      y = clientY - box.top;
    return (
      this.aiko.visible &&
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
      this.floorPoint(x, y)?.depth ?? this.petPosition?.depth ?? 300,
    );
  }
  portionSizeAt(definition: string, depth: number, x?: number): [number, number] {
    const dimensions = this.assets.items[definition]?.dimensions ?? [72, 72];
    const point = { x: x ?? this.petPosition?.x ?? 400, depth };
    const projected = this.camera.projection.projectPoint(point);
    const scale =
      projected.depth > 50
        ? projected.scale
        : this.camera.projection.projectPoint(this.callPoint()).scale;
    const factor =
      ((scale * this.assets.layout.pet_height) / this.assets.characterHeight) *
      (this.assets.items[definition]?.worldZoom ?? 1);
    return [dimensions[0]! * factor, dimensions[1]! * factor];
  }
  objectDepth(instance: string): number {
    return new Map(this.snapshot?.room.object_depths).get(instance) ?? 300;
  }
  dragPoint(
    clientX: number,
    clientY: number,
    ground: RoomPoint,
    definition: string,
  ): DragPlacement {
    const box = this.app.canvas.getBoundingClientRect();
    const x = clientX - box.left,
      y = clientY - box.top;
    const asset = this.assets.items[definition]!;
    const support =
      ((asset.dimensions[1] - asset.pivot[1]) *
        this.portionSizeAt(definition, ground.depth, ground.x)[1]) /
      asset.dimensions[1];
    const overPet = this.petContains(clientX, clientY);
    const previous = ground;
    const projection = this.camera.projection;
    const floor = this.picking.resolveDrop(
      x,
      Math.min(
        y + support + 24 * projection.fit,
        projection.floorFront * projection.fit,
      ),
    );
    const held = this.picking.atDepth(
      x,
      y + support,
      overPet ? this.petPosition! : previous,
    );
    const groundProjection = floor && projection.projectPoint(floor);
    const placement = overPet
      ? held
      : floor && groundProjection
        ? {
            point: floor,
            height: Math.max(
              0,
              (groundProjection.y - y - support) / groundProjection.scale,
            ),
          }
        : held;
    const point = placement?.point ?? previous;
    const pet = this.aiko.screenBounds(),
      width = Math.max(1, pet.scale * 192);
    const inside =
      x >= 0 && x <= box.width && y >= 0 && y <= this.camera.sceneHeight && !!placement;
    return {
      ...point,
      height: placement?.height ?? 0,
      inside,
      offer: inside && overPet,
      face_x: (x - pet.originX - pet.scale * 96) / width,
      face_y: (y - pet.originY - pet.scale * 100) / width,
    };
  }
  followPet(callback: (bounds: PetScreenBounds) => void): () => void {
    this.followers.add(callback);
    return () => this.followers.delete(callback);
  }
  tableGameFrame() {
    const table = this.assets.layout.furniture.find((item) => item.id === 'table');
    return table && tableGameFrame(furnitureFrame(this.camera.projection, table));
  }
  frameForGame(id: string): void {
    this.camera.setGame(true, id === 'connect_four');
    const table = this.assets.layout.furniture.find((item) => item.id === 'table');
    if (id === 'connect_four' && table) {
      this.camera.releaseFollow();
      this.camera.lookAt({ x: table.x, depth: table.z + table.depth * 0.2 });
    } else if (this.petPosition) this.camera.lookAt(this.petPosition);
  }
  floorPoint(clientX: number, clientY: number): RoomPoint | undefined {
    const box = this.app.canvas.getBoundingClientRect();
    const x = clientX - box.left,
      y = clientY - box.top;
    if (x < 0 || x > box.width || y < 0 || y > this.camera.sceneHeight) return;
    return this.picking.resolveDrop(x, y);
  }
  callPoint(): RoomPoint {
    return this.camera.projection.pointAtBearing(this.camera.yaw, 180);
  }
  get petPosition(): RoomPoint | undefined {
    return this.snapshot?.room.pet;
  }
  get heldGameChip(): boolean {
    return this.snapshot?.held_item === 'c4-red';
  }
  get petVisible(): boolean {
    if (!this.snapshot || !this.aiko.visible) return false;
    const b = this.aiko.screenBounds();
    return (
      b.x + b.width > 0 &&
      b.x < this.host.clientWidth &&
      b.y + b.height > 0 &&
      b.y < this.camera.sceneHeight
    );
  }
  destroy(): void {
    this.disposed = true;
    this.camera.destroy();
    this.followers.clear();
    this.resizeObserver?.disconnect();
    this.app.destroy(true, { children: true });
  }
}
