import type { RoomSnapshot } from '../bridge/RoomClient';
import type { RoomView } from '../room/RoomView';
import { button, element } from './dom';

export interface FoodChoice {
  id: string;
  display_name: string;
}

export function foodImage(
  room: RoomView,
  food: FoodChoice,
): HTMLImageElement | undefined {
  const asset = room.assets.items[food.id];
  if (!asset) return;
  const image = element('img');
  image.src = new URL(asset.file, room.root).href;
  image.alt = '';
  image.draggable = false;
  return image;
}

export class FoodPanel {
  readonly element = element('section', 'food-panel');
  constructor(
    snapshot: RoomSnapshot,
    room: RoomView,
    select: (food: FoodChoice) => void,
  ) {
    const foods = snapshot.catalog.foods as FoodChoice[];
    const grid = element('div', 'food-choices');
    for (const food of [
      ...foods,
      { id: 'energy_drink', display_name: 'Energy Drink' },
    ]) {
      const choose = button(food.display_name, () => select(food));
      choose.className = 'food-choice';
      const image = foodImage(room, food);
      if (image) choose.prepend(image);
      grid.append(choose);
    }
    this.element.append(grid);
  }
}
