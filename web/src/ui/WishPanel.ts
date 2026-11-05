import type { RoomSnapshot } from '../bridge/RoomClient';
import { button,element,line } from './dom';
import type { Command } from './dom';

export class WishPanel {
  readonly element=element('section');
  constructor(private command:Command){}
  update(snapshot:RoomSnapshot):void {
    this.element.replaceChildren();
    const status=snapshot.catalog.status as {emotional?:{wishes:Array<{label:string;description:string;target_label:string;restriction_label:string;value:{instance_id:number;pinned:boolean}} >}}|undefined;
    const wishes=status?.emotional?.wishes??[];
    if(!wishes.length)this.element.append(line('Aiko hat gerade keinen Wunsch.'));
    for(const wish of wishes){
      const row=element('article','wish');row.append(element('h3','',wish.label),line(wish.description),line(wish.target_label));
      if(wish.restriction_label)row.append(line(wish.restriction_label));
      row.append(button(wish.value.pinned?'Lösen':'Merken',()=>{void this.command('wish_pin',{id:wish.value.instance_id,pinned:!wish.value.pinned});}),
        button('Verwerfen',()=>{void this.command('wish_dismiss',{id:wish.value.instance_id});}));
      this.element.append(row);
    }
  }
}
