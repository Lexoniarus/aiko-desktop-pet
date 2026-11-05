import { button,element } from '../ui/dom';
import type { Command } from '../ui/dom';
import { GameFrame,record,values } from './GameView';
import type { GameView } from './GameView';

export class BlackjackView extends GameFrame implements GameView {
  private table=element('div','blackjack-table');
  private hit=button('Karte',()=>this.action('hit'));
  private stand=button('Bleiben',()=>this.action('stand'));
  constructor(command:Command,private root:string){super(command);this.content.append(this.table,this.hit,this.stand);}
  update(data:Record<string,unknown>):void {
    this.scoreline(data.score);const table=record(data.table);this.table.replaceChildren();
    for(const [title,key] of [['Aiko','dealer'],['Du','player']]){
      const hand=element('div','card-hand');hand.append(element('h3','',title!));
      for(const value of values(table[key!])){const card=record(value),image=element('img');image.src=new URL(`assets/playing_cards/${value?`card_${card.suit}_${card.rank}.png`:'card_back.png'}`,this.root).href;image.alt=value?`${card.rank} ${card.suit}`:'Verdeckte Karte';hand.append(image);}
      this.table.append(hand);
    }
    this.table.append(element('p','',`Deine Punkte: ${table.player_total??'–'}`));
    const allowed=table.phase==='player'&&!data.busy;this.hit.disabled=this.stand.disabled=!allowed;
    if(table.result)this.table.append(element('p','game-result',table.result==='win'?'Du gewinnst.':table.result==='loss'?'Aiko gewinnt.':'Unentschieden.'));
  }
}
