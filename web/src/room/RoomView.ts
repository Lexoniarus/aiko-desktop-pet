import { Application, Assets, Container, Sprite, Texture } from 'pixi.js';
import type { FederatedPointerEvent } from 'pixi.js';
import { Viewport } from 'pixi-viewport';
import type { RoomSnapshot } from '../bridge/RoomClient';
import { AikoView } from './AikoView';
import type { Clip } from './AikoView';
import { RoomCamera } from './RoomCamera';
import { depthScale, feetY, projectX, unproject, wrap } from './RoomProjection';

export interface AssetManifest {
  clips: Record<string, Clip>;
  items: Record<string, { file: string; label: string; pivot: [number,number]; states?:Record<string,string> }>;
  room: Record<string, string>;
}
type WorldItem = RoomSnapshot['objects'][number];
const cutouts: Record<string, { crop: number[]; width: number; x: number; y: number }> = {
  bed: { crop: [56,126,1659,665], width: 680, x: 4780, y: 820 },
  desk: { crop: [44,178,1265,821], width: 386, x: 4240, y: 820 },
  shelf: { crop: [124,122,1121,923], width: 270, x: 3920, y: 540 },
  plant: { crop: [94,84,943,1245], width: 204, x: 3750, y: 810 },
  table: { crop: [216,138,1741,489], width: 527, x: 2450, y: 880 },
  fridge: { crop: [140,130,760,1350], width: 244, x: 1425, y: 802 },
  door: { crop: [163,107,698,1319], width: 230, x: 315, y: 784 },
  kitchenUnit: { crop: [115,85,1810,1415], width: 760, x: 930, y: 820 },
};

export class RoomView {
  readonly app = new Application();
  camera!: RoomCamera;
  private world = new Container();
  private aiko!: AikoView;
  private viewport!: Viewport;
  private objects = new Map<string, { sprite: Sprite; item: WorldItem }>();
  private snapshot?: RoomSnapshot;
  onObjectDown: (item: WorldItem, event: FederatedPointerEvent) => void = () => {};
  onPetTap: () => void = () => {};
  private resizeObserver?: ResizeObserver;

  constructor(private host: HTMLElement, readonly root: string, readonly assets: AssetManifest) {}

  async initialize(): Promise<void> {
    await this.app.init({ resizeTo: this.host, background: '#f7f2f3', antialias: true,
      resolution: Math.min(2, devicePixelRatio), autoDensity: true, preference: 'webgl' });
    this.host.append(this.app.canvas);
    this.viewport = new Viewport({ screenWidth: this.host.clientWidth, screenHeight: this.host.clientHeight,
      worldWidth: 15300, worldHeight: 900, events: this.app.renderer.events });
    this.app.stage.addChild(this.viewport);
    this.camera = new RoomCamera(this.viewport);
    this.world.sortableChildren = true;
    this.viewport.addChild(this.world);
    const imageEntries = await Promise.all(Object.entries(this.assets.room).map(async ([id, file]) => {
      const image = new Image(); image.src = new URL(`room/${file}`, this.root).href;
      await image.decode(); return [id, image] as const;
    }));
    const images = Object.fromEntries(imageEntries);
    const background = document.createElement('canvas'); background.width = 5100; background.height = 900;
    const ctx = background.getContext('2d')!;
    ctx.drawImage(images.kitchen!, 0, 0, 1800, 900);
    ctx.drawImage(images.living!, 1800, 0, 1800, 900);
    const wall = images.kitchen!;
    ctx.drawImage(wall, 0, 0, 1500 * wall.height / 900, wall.height, 3600, 0, 1500, 900);
    ctx.fillStyle = 'rgba(255,243,252,.33)';
    for (const [x,y,w,h] of [[0,0,1800,38],[20,65,185,690],[1125,65,675,240],[1125,305,310,170],[1580,305,220,170],[1125,475,675,280]]) {
      ctx.fillRect(1800+x!, y!, w!, h!);
    }
    const texture = Texture.from(background);
    for (const offset of [-5100, 0, 5100]) {
      const tile = new Sprite(texture); tile.x = offset; tile.zIndex = -10000; this.world.addChild(tile);
      for (const [name, definition] of Object.entries(cutouts)) {
        const source = images[name]!;
        const [x,y,w,h] = definition.crop as [number,number,number,number];
        const canvas = document.createElement('canvas'); canvas.width = w; canvas.height = h;
        canvas.getContext('2d')!.drawImage(source,x,y,w,h,0,0,w,h);
        const furniture = new Sprite(Texture.from(canvas)); furniture.anchor.set(.5,1);
        furniture.width = definition.width; furniture.height = h / w * definition.width;
        furniture.position.set(offset+definition.x,definition.y);
        furniture.zIndex = name === 'table' ? definition.y : -1000;
        this.world.addChild(furniture);
      }
    }
    this.aiko = new AikoView(this.root, this.assets.clips, this.assets.items);
    this.aiko.on('pointertap', () => this.onPetTap());
    this.world.addChild(this.aiko);
    await this.aiko.show('idle');
    this.resizeObserver = new ResizeObserver(() => this.camera.resize(this.host.clientWidth,this.host.clientHeight));
    this.resizeObserver.observe(this.host);
    this.camera.resize(this.host.clientWidth,this.host.clientHeight);
    this.camera.lookAt(600);
    this.app.ticker.add(() => this.draw());
  }

  async update(snapshot: RoomSnapshot): Promise<void> {
    this.snapshot = snapshot;
    void this.aiko.show(snapshot.animation,snapshot.animation_id);
    void this.aiko.hold(snapshot.held_item??null,snapshot.held_pose);
    const live = new Set(snapshot.objects.filter(item => !['consumed','removed'].includes(item.state)).map(item => item.instance_id));
    for (const [id, current] of this.objects) if (!live.has(id)) {
      current.sprite.destroy(); this.objects.delete(id);
    }
    for (const item of snapshot.objects) {
      if (!live.has(item.instance_id) || this.objects.has(item.instance_id)) {
        const known = this.objects.get(item.instance_id); if (known) known.item = item;
        continue;
      }
      const asset = this.assets.items[item.definition_id]; if (!asset) continue;
      const texture = await Assets.load<Texture>(new URL(asset.file,this.root).href);
      if (this.objects.has(item.instance_id)) continue;
      const sprite = new Sprite(texture); sprite.anchor.set(.5,1); sprite.eventMode = 'static'; sprite.cursor = 'grab';
      sprite.on('pointerdown', event => { const current=this.objects.get(item.instance_id); if (current) this.onObjectDown(current.item,event); });
      this.world.addChild(sprite); this.objects.set(item.instance_id,{sprite,item});
    }
    this.draw();
  }

  private draw(): void {
    const snapshot = this.snapshot; if (!snapshot) return;
    const center = this.viewport.center.x;
    const point = snapshot.room.pet;
    this.aiko.position.set(projectX(point.x, point.depth, center), feetY(point.depth));
    this.aiko.scale.set(400/416*depthScale(point.depth));
    this.aiko.zIndex = feetY(point.depth);
    const depths = new Map(snapshot.room.object_depths);
    for (const {sprite,item} of this.objects.values()) {
      const position = item.position;
      sprite.visible = position !== null && item.state !== 'pet_held';
      if (!position) continue;
      const depth = depths.get(item.instance_id) ?? .9;
      sprite.position.set(projectX(position.x,depth,center),feetY(depth)-position.height);
      sprite.scale.set(depthScale(depth)); sprite.zIndex = feetY(depth);
    }
  }

  pointAt(clientX: number, clientY: number): { x: number; depth: number } {
    const box = this.app.canvas.getBoundingClientRect();
    const world = this.viewport.toWorld(clientX-box.left,clientY-box.top);
    return unproject(world.x,world.y,this.viewport.center.x);
  }
  callPoint(): {x:number;depth:number} { return {x:wrap(this.viewport.center.x),depth:1.1}; }
  get petPosition(): {x:number;depth:number} | undefined { return this.snapshot?.room.pet; }
  destroy(): void { this.resizeObserver?.disconnect(); this.app.destroy(true,{children:true}); }
}
