import type { RoomSnapshot } from '../bridge/RoomClient';
import type { RoomView } from '../room/RoomView';
import type { ObjectDragController } from '../input/ObjectDragController';
import { button, element, line } from './dom';
import type { Command } from './dom';

export class FoodPanel {
  readonly element=element('section','food-panel');
  constructor(snapshot:RoomSnapshot,room:RoomView,drag:ObjectDragController,command:Command) {
    this.element.append(line('Ziehe eine Portion ins Zimmer oder biete sie Aiko direkt an.'));
    const foods=snapshot.catalog.foods as Array<{id:string;display_name:string}>;
    const grid=element('div','food-choices');
    for(const food of [...foods,{id:'energy_drink',display_name:'Energy Drink'}]){
      const row=element('div','food-choice');
      const choose=element('button','food-drag',food.display_name);choose.type='button';
      const asset=room.assets.items[food.id];
      if(asset){const image=element('img');image.src=new URL(asset.file,room.root).href;image.alt='';image.draggable=false;choose.prepend(image);}
      choose.setAttribute('aria-label',`${food.display_name} ins Zimmer ziehen`);
      drag.bindSupply(choose,food.id);
      const offer=button('Anbieten',()=>{void command('offer',{definition:food.id});});
      row.append(choose,offer);grid.append(row);
    }
    this.element.append(grid);
  }
}
