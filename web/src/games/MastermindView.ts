import { button,element } from '../ui/dom';
import type { Command } from '../ui/dom';
import { GameFrame,record,values } from './GameView';
import type { GameView } from './GameView';

export class MastermindView extends GameFrame implements GameView {
  private guesses=element('div','mm-history');private code=element('div','mm-code');
  private slots=element('div','mm-slots');private palette=element('div','mm-palette');
  private selected:(string|null)[]=[null,null,null,null];private index=0;private count=0;
  private submit=button('Prüfen',()=>this.action('submit',this.selected));private nextButton=this.next();
  private dragging:string|undefined;private release:(event:PointerEvent)=>void;
  constructor(command:Command){
    super(command);this.release=event=>{const slot=document.elementFromPoint(event.clientX,event.clientY)?.closest<HTMLElement>('[data-mm-slot]');if(slot&&this.dragging){this.selected[Number(slot.dataset.mmSlot)]=this.dragging;this.drawSlots();}this.dragging=undefined;};
    window.addEventListener('pointerup',this.release);this.content.append(this.code,this.guesses,this.slots,this.palette,this.submit,this.nextButton);this.drawSlots();
  }
  private drawSlots():void {
    this.slots.replaceChildren();this.selected.forEach((value,index)=>{const pin=button(value??'?',()=>{this.index=index;this.drawSlots();});pin.dataset.mmSlot=String(index);pin.dataset.color=value??'';pin.className='mm-pin';pin.classList.toggle('selected',this.index===index);pin.setAttribute('aria-label',`Position ${index+1}: ${value??'leer'}`);this.slots.append(pin);});this.submit.disabled=this.selected.some(value=>value===null);
  }
  update(data:Record<string,unknown>):void {
    this.scoreline(data.score);const view=record(data.view),guesses=values(view.guesses);
    if(guesses.length!==this.count){this.count=guesses.length;this.selected=[null,null,null,null];this.index=0;this.drawSlots();}
    if(!this.palette.children.length){for(const color of values(data.colors)){const value=String(color),control=button(value,()=>{this.selected[this.index]=value;this.index=(this.index+1)%4;this.drawSlots();});control.className='mm-pin';control.dataset.color=value;control.addEventListener('pointerdown',()=>{this.dragging=value;});this.palette.append(control);}}
    this.guesses.replaceChildren();for(const [index,entry] of guesses.entries()){const guess=record(entry),row=element('div','mm-guess');for(const color of values(guess.colors)){const pin=element('span','mm-pin');pin.dataset.color=String(color);pin.setAttribute('aria-label',String(color));row.append(pin);}const feedback=record(guess.feedback);const available=index===guesses.length-1?Number(data.feedback_count??0):4;row.append(element('span','',`${Math.min(Number(feedback.exact??0),available)} exakt · ${Math.max(0,Math.min(Number(feedback.misplaced??0),available-Number(feedback.exact??0)))} versetzt`));this.guesses.append(row);}
    this.code.replaceChildren();for(const color of values(record(data.code).slots)){const pin=element('span','mm-pin',color?'':'?');if(color)pin.dataset.color=String(color);this.code.append(pin);}
    this.submit.disabled=!!data.busy||!!view.result||this.selected.some(value=>value===null);
    this.nextButton.hidden=!view.result;for(const control of this.palette.querySelectorAll('button'))control.disabled=!!data.busy||!!view.result;
  }
  destroy():void {window.removeEventListener('pointerup',this.release);}
}
