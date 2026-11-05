import { Viewport } from 'pixi-viewport';
import { roomWidth, wrap } from './RoomProjection';

export class RoomCamera {
  constructor(readonly viewport: Viewport) {
    viewport.drag({ direction: 'x' }).decelerate({ friction: .92 });
    viewport.on('moved', () => {
      const x = viewport.center.x;
      if (x < 0 || x >= roomWidth) viewport.moveCenter(wrap(x), 450);
      viewport.y = (viewport.screenHeight - 900 * viewport.scale.y) / 2;
    });
  }
  resize(width: number, height: number): void {
    const center = this.viewport.center.x;
    this.viewport.resize(width, height, roomWidth * 3, 900);
    this.viewport.fitHeight(900);
    this.viewport.moveCenter(center, 450);
  }
  lookAt(x: number): void { this.viewport.moveCenter(wrap(x), 450); }
  hold(held: boolean): void {
    if (held) { this.viewport.plugins.pause('drag'); this.viewport.plugins.pause('decelerate'); }
    else { this.viewport.plugins.resume('drag'); this.viewport.plugins.resume('decelerate'); }
  }
}
