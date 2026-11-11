import type { ObjectDragController } from '../input/ObjectDragController';
import type { RoomView } from '../room/RoomView';
import { button, element } from './dom';
import { foodImage, type FoodChoice } from './FoodPanel';

export class FoodTray {
  readonly element = element('section', 'food-tray');

  constructor(
    private room: RoomView,
    private drag: ObjectDragController,
  ) {
    this.element.hidden = true;
    this.element.setAttribute('aria-label', 'Ablage für Futter');
  }

  select(food: FoodChoice): void {
    const portion = element('div', 'food-portion', `${food.display_name} ziehen`);
    const image = foodImage(this.room, food);
    if (image) portion.prepend(image);
    const putBack = button('×', () => this.clear());
    putBack.setAttribute('aria-label', 'Portion zurücklegen');
    this.drag.bindSupply(portion, food.id, () => {
      if (portion.parentElement === this.element) this.clear();
    });
    this.element.replaceChildren(portion, putBack);
    this.element.hidden = false;
  }

  clear(): void {
    this.element.hidden = true;
    this.element.replaceChildren();
  }

  setPanning(panning: boolean): void {
    if (!this.element.hidden) this.element.toggleAttribute('data-panning', panning);
  }
}
