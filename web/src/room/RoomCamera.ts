import { Viewport } from 'pixi-viewport';
import { roomWidth, wrap } from './RoomProjection';

export class RoomCamera {
  private gameOpen = false;
  get portraitGame(): boolean {
    return this.gameOpen && this.viewport.screenHeight > this.viewport.screenWidth;
  }
  private get sceneHeight(): number {
    return this.portraitGame
      ? this.viewport.screenHeight * 0.48 - 88
      : this.viewport.screenHeight;
  }
  constructor(readonly viewport: Viewport) {
    viewport.drag({ direction: 'x' }).decelerate({ friction: 0.92 });
    viewport.on('moved', () => {
      const x = viewport.center.x;
      if (x < 0 || x >= roomWidth) viewport.moveCenter(wrap(x), 450);
      viewport.y = (this.sceneHeight - 900 * viewport.scale.y) / 2;
    });
  }
  resize(width: number, height: number): void {
    const center = this.viewport.center.x;
    this.viewport.resize(width, height, roomWidth * 3, 900);
    this.viewport.scale.set(Math.max(180, this.sceneHeight) / 900);
    this.viewport.moveCenter(center, 450);
    this.viewport.y = 0;
  }
  lookAt(x: number): void {
    this.viewport.moveCenter(wrap(x), 450);
    this.viewport.y = 0;
  }
  setGame(open: boolean): void {
    if (this.gameOpen === open) return;
    this.gameOpen = open;
    this.resize(this.viewport.screenWidth, this.viewport.screenHeight);
  }
  hold(held: boolean): void {
    if (held) {
      this.viewport.plugins.get('decelerate')?.reset();
      this.viewport.plugins.pause('drag');
      this.viewport.plugins.pause('decelerate');
    } else {
      this.viewport.plugins.resume('drag');
      this.viewport.plugins.resume('decelerate');
    }
  }
}
