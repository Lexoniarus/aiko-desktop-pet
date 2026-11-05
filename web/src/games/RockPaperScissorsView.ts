import { element } from '../ui/dom';
import type { Command } from '../ui/dom';
import { GameFrame } from './GameView';
import type { GameView } from './GameView';

export class RockPaperScissorsView extends GameFrame implements GameView {
  private hands=element('div','rps-hands');
  private choices:HTMLButtonElement[]=[];
  constructor(command:Command,private root:string){
    super(command);this.content.append(this.hands);
    const choices=element('div','rps-choices');
    for(const [id,label] of [['rock','Stein'],['paper','Papier'],['scissors','Schere']]){
      const control=element('button','',label!);const image=element('img');image.src=new URL(`assets/game_hands/${id}.png`,root).href;image.alt='';control.prepend(image);
      control.addEventListener('click',()=>this.action('choose',id));choices.append(control);this.choices.push(control);
    }
    this.content.append(choices);
  }
  update(data:Record<string,unknown>):void {
    this.scoreline(data.score);this.hands.replaceChildren();
    const labels:Record<string,string>={rock:'Stein',paper:'Papier',scissors:'Schere'};
    for(const [owner,key] of [['Du','player'],['Aiko','aiko']]){
      const hand=element('div','rps-hand');hand.append(element('strong','',owner!));
      const value=data[key!];if(typeof value==='string'){const image=element('img');image.src=new URL(`assets/game_hands/${value}.png`,this.root).href;image.alt=labels[value]??value;hand.append(image);}else hand.append(element('span','','?'));
      this.hands.append(hand);
    }
    for(const control of this.choices)control.disabled=!!data.busy;
  }
}
