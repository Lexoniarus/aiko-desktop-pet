import type { RoomSnapshot } from '../bridge/RoomClient';
import { element,line } from './dom';

export class StatusPanel {
  readonly element=element('section');
  update(snapshot:RoomSnapshot):void {
    this.element.replaceChildren();
    const status=snapshot.catalog.status as Record<string,unknown> | undefined;
    const values=status?.status_values as Array<[string,number]> | undefined;
    const labels:Record<string,string>={satiety:'Sättigung',energy:'Energie',fun:'Spaß',social:'Geselligkeit',affection:'Zuneigung',mood:'Stimmung',friendship:'Freundschaft'};
    for(const [key,value] of values??Object.entries(snapshot.pet).filter((entry):entry is [string,number]=>entry[0] in labels&&typeof entry[1]==='number')){
      const row=element('label','need-row',`${labels[key]??key} ${Math.round(value)}`);
      const meter=element('meter');meter.min=0;meter.max=100;meter.value=value;row.append(meter);this.element.append(row);
    }
    if(status){
      for(const field of ['relationship_line','wellbeing_line','sleep_context_line','contact_line','hint','objects_line']){
        if(status[field])this.element.append(line(String(status[field])));
      }
      const emotional=status.emotional as {state_label:string;moodlets:Array<{label:string;description:string}>};
      this.element.append(element('h3','',emotional.state_label));
      for(const moodlet of emotional.moodlets){const detail=element('details');detail.append(element('summary','',moodlet.label),line(moodlet.description));this.element.append(detail);}
    }
  }
}
