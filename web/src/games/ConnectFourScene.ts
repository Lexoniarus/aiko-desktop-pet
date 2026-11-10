import { Assets, Container, Graphics, Sprite, Texture } from 'pixi.js';
import type { PetScreenBounds } from '../room/AikoView';
import type { TableGameFrame } from './ConnectFourGeometry';
import { cellPoint, chipPoint, connectFourGeometry as g } from './ConnectFourGeometry';
import { record, values } from './GameView';

/** All visible game art participates in the room's floor-depth ordering. */
export class ConnectFourScene {
  readonly ready: Promise<void>;
  private board = new Container({
    label: 'connect-four-board',
    sortableChildren: true,
  });
  private face = new Sprite(Texture.EMPTY);
  private cells = Array.from({ length: 42 }, () => new Sprite(Texture.EMPTY));
  private moving = new Sprite(Texture.EMPTY);
  private preview = new Sprite(Texture.EMPTY);
  private marks = new Graphics();
  private player = new Container({ label: 'connect-four-player-supply' });
  private aiko = new Container({ label: 'connect-four-aiko-supply' });
  private flight = new Sprite(Texture.EMPTY);
  private dragged = new Sprite(Texture.EMPTY);
  private textures: Texture[] = [];
  private data: Record<string, unknown> = {};
  private received = 0;
  private flightKey: unknown;
  private flightStart = { x: 0, y: 0 };
  private disposed = false;

  constructor(world: Container, root: string) {
    this.face.zIndex = 2;
    this.moving.zIndex = 1;
    this.preview.zIndex = 3;
    this.preview.alpha = 0.65;
    this.marks.zIndex = 4;
    this.board.addChild(
      ...this.cells,
      this.moving,
      this.face,
      this.preview,
      this.marks,
    );
    this.flight.label = 'connect-four-flight';
    this.dragged.label = 'connect-four-drag';
    for (let i = 0; i < 3; i++) {
      this.player.addChild(new Sprite(Texture.EMPTY));
      this.aiko.addChild(new Sprite(Texture.EMPTY));
    }
    for (const view of [
      this.board,
      this.player,
      this.aiko,
      this.flight,
      this.dragged,
    ]) {
      view.eventMode = 'none';
      view.visible = false;
      world.addChild(view);
    }
    this.ready = Promise.all(
      ['c4-board', 'c4-yellow', 'c4-red', 'c4-pile'].map((name) =>
        Assets.load<Texture>(new URL(`assets/game_frontends/${name}.png`, root).href),
      ),
    ).then((textures) => {
      if (this.disposed) return;
      this.textures = textures;
      this.face.texture = textures[0]!;
      this.face.width = this.face.height = g.size;
    });
  }

  update(data: Record<string, unknown>): void {
    this.data = data;
    this.received = performance.now();
  }

  private chip(
    sprite: Sprite,
    texture: Texture,
    x: number,
    y: number,
    size: number,
  ): void {
    sprite.texture = texture;
    sprite.anchor.set(0.5);
    sprite.position.set(x, y);
    sprite.width = size;
    sprite.height = (size * texture.height) / texture.width;
  }

  draw(
    frame: TableGameFrame,
    bounds: PetScreenBounds,
    heldChip: boolean,
    previewCell?: number,
    drag?: { x: number; y: number },
  ): void {
    if (this.disposed || this.textures.length === 0) return;
    const [, yellow, red, pile] = this.textures as [Texture, Texture, Texture, Texture];
    this.board.visible = this.player.visible = true;
    this.board.position.set(frame.x, frame.y);
    this.board.scale.set(frame.scale);
    this.board.zIndex = frame.order + 0.01;
    const board = record(this.data.board),
      cells = values(board.cells);
    const winning = values(board.winning_line ?? board.winning_cells);
    const motion = record(record(this.data.props).motion),
      drop = record(this.data.drop);
    const hidden = Number(motion.kind === 'chip' ? motion.cell : (drop.cell ?? -1));
    this.marks.clear();
    this.cells.forEach((sprite, index) => {
      const owner = Number(cells[index] ?? 0),
        point = cellPoint(index);
      sprite.visible = !!owner && index !== hidden;
      sprite.zIndex = 1;
      this.chip(sprite, owner === 1 ? yellow : red, point.x, point.y, g.chip);
      if (sprite.visible && winning.includes(index))
        this.marks
          .circle(point.x, point.y, g.chip / 2 + 2)
          .stroke({ color: 0x755c93, width: 3 });
    });
    this.preview.visible = previewCell !== undefined;
    if (previewCell !== undefined) {
      const point = cellPoint(previewCell);
      this.chip(this.preview, yellow, point.x, g.entry, g.chip);
      const radius = g.chip / 2 - 1;
      for (let i = 0; i < 8; i++)
        this.marks
          .moveTo(
            point.x + radius * Math.cos((i * Math.PI) / 4),
            point.y + radius * Math.sin((i * Math.PI) / 4),
          )
          .arc(point.x, point.y, radius, (i * Math.PI) / 4, ((i + 0.6) * Math.PI) / 4)
          .stroke({ color: 0x755c93, width: 3 });
    }
    this.player.position.set(frame.playerX, frame.playerY);
    this.player.zIndex = frame.playerY + 0.01;
    this.aiko.visible = !this.data.preparing;
    this.aiko.position.set(
      bounds.originX + 80 * bounds.scale,
      bounds.groundY + frame.chip * 0.4,
    );
    this.aiko.zIndex = bounds.groundY + 0.02;
    this.player.children.forEach((child, i) => {
      this.chip(child as Sprite, yellow, 0, -i * 4, frame.chip);
      (child as Sprite).height *= 0.55;
    });
    this.aiko.children.forEach((child, i) => {
      child.visible = i !== 2 || (!heldChip && motion.kind !== 'chip');
      this.chip(child as Sprite, pile, 0, -i * 4 * frame.scale, frame.chip);
    });
    this.moving.visible = this.flight.visible = false;
    const elapsed = performance.now() - this.received;
    if (motion.kind === 'chip') {
      if (motion.id !== this.flightKey) {
        this.flightKey = motion.id;
        this.flightStart = {
          x: (bounds.originX + 96 * bounds.scale - frame.x) / frame.scale,
          y: (bounds.originY + 141 * bounds.scale - frame.y) / frame.scale,
        };
      }
      const fraction = Math.min(
        1,
        Number(motion.fraction) + elapsed / Number(motion.duration),
      );
      const seam = Number(motion.flight_duration) / Number(motion.duration);
      const point = chipPoint(this.flightStart, Number(motion.cell), fraction, seam);
      if (fraction < seam) {
        this.flight.visible = true;
        this.chip(
          this.flight,
          red,
          frame.x + point.x * frame.scale,
          frame.y + point.y * frame.scale,
          frame.chip,
        );
        const t = fraction / seam;
        this.flight.zIndex = bounds.groundY * (1 - t) + frame.order * t + 0.03;
      } else {
        this.moving.visible = true;
        this.chip(this.moving, red, point.x, point.y, g.chip);
      }
    } else if (Number(drop.cell ?? -1) >= 0 && Number(drop.fraction) >= 0) {
      const target = cellPoint(Number(drop.cell));
      const t = Math.min(1, Number(drop.fraction) + elapsed / 180);
      this.moving.visible = true;
      this.chip(
        this.moving,
        Number(drop.player) === 1 ? yellow : red,
        target.x,
        g.entry + (target.y - g.entry) * t,
        g.chip,
      );
    }
    this.dragged.visible = !!drag;
    if (drag) {
      this.chip(
        this.dragged,
        yellow,
        frame.x + drag.x * frame.scale,
        frame.y + drag.y * frame.scale,
        frame.chip,
      );
      this.dragged.zIndex = 10000;
    }
  }

  destroy(): void {
    this.disposed = true;
    for (const view of [this.board, this.player, this.aiko, this.flight, this.dragged])
      view.destroy({ children: true });
  }
}
