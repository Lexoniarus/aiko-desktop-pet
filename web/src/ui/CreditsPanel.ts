import type { RoomSnapshot } from '../bridge/RoomClient';
import { element,line,link } from './dom';

export class CreditsPanel {
  readonly element=element('section');
  constructor(snapshot:RoomSnapshot,root:string){
    this.element.append(line('Aiko Desktop Pet · Gemeinsames Zimmer'),link('Lizenzen und Bildrechte',new URL('licenses/ASSETS.md',root).href));
    const social=snapshot.social as [string,{source?:string;source_url?:string;permalink?:string;author?:string}]|undefined;
    const content=social?.[1];
    if(content){this.element.append(line(content.source??''));if(content.author)this.element.append(line(content.author));if(content.source_url)this.element.append(link('Quelle',content.source_url));if(content.permalink)this.element.append(link('Original',content.permalink));}
  }
}
