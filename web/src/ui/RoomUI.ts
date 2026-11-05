import type { RoomSnapshot } from '../bridge/RoomClient';
import type { RoomView } from '../room/RoomView';
import type { ObjectDragController } from '../input/ObjectDragController';
import { FoodPanel } from './FoodPanel';
import { SocialPanel } from './SocialPanel';
import { StatusPanel } from './StatusPanel';
import { WishPanel } from './WishPanel';
import { SettingsPanel } from './SettingsPanel';
import { CreditsPanel } from './CreditsPanel';
import { RockPaperScissorsView } from '../games/RockPaperScissorsView';
import { TicTacToeView } from '../games/TicTacToeView';
import { BlackjackView } from '../games/BlackjackView';
import { ConnectFourView } from '../games/ConnectFourView';
import { MastermindView } from '../games/MastermindView';
import { QuizView } from '../games/QuizView';
import type { GameView } from '../games/GameView';
import { button,element } from './dom';
import type { Command } from './dom';

export class RoomUI {
  private toolbar=element('nav','room-toolbar');
  private dialogue=element('div','room-speech');
  private text=element('p');private emote=element('span','speech-emote');
  private next=button('Weiter',()=>{void this.command('speech_next');});
  private panel=element('dialog','room-panel');private panelBody=element('div','panel-body');
  private title=element('h2');private snapshot?:RoomSnapshot;private panelName='';
  private activePanel:StatusPanel|WishPanel|undefined;
  private game:GameView|undefined;private gameId='';private gameSignature='';private speechId=-1;
  private pet=button('Streicheln',()=>{void this.command('care',{action:'pet'});});
  private sleep=button('Schlafen',()=>{void this.command('care',{action:'sleep'});});
  readonly status=element('div','room-message');
  constructor(private host:HTMLElement,private room:RoomView,private drag:ObjectDragController,private command:Command){
    this.toolbar.setAttribute('aria-label','Aikos Zimmer');
    for(const [name,label] of [['food','Füttern'],['games','Spielen'],['social','Plaudern'],['status','Befinden'],['wishes','Wünsche'],['settings','Einstellungen']])this.toolbar.append(button(label!,()=>{this.open(name!);}));
    this.toolbar.prepend(button('Aiko rufen',()=>{void command('call',room.callPoint());}));
    this.dialogue.setAttribute('aria-live','polite');this.dialogue.append(this.emote,this.text,this.next);this.dialogue.hidden=true;
    this.status.setAttribute('role','status');
    const care=element('div','quick-care');care.append(this.pet,this.sleep,button('Aiko finden',()=>{const point=this.room.petPosition;if(point)this.room.camera.lookAt(point.x);}));
    const header=element('header','panel-header');header.append(this.title,button('Schließen',()=>{this.close();}));this.panel.append(header,this.panelBody);this.panel.setAttribute('aria-label','Aikos Zimmermenü');
    this.panel.addEventListener('cancel',event=>{event.preventDefault();this.close();});
    drag.onDragBegin=()=>{this.panel.close();this.panelName='';this.activePanel=undefined;};
    host.append(this.toolbar,care,this.dialogue,this.panel,this.status);
  }
  private open(name:string):void {
    const snapshot=this.snapshot;if(!snapshot)return;
    if(this.gameId&&name!=='games'){void this.command('game_close').then(()=>this.open(name));return;}
    this.panelName=name;this.activePanel=undefined;this.panelBody.replaceChildren();
    const titles:Record<string,string>={food:'Füttern',games:'Spielen',social:'Plaudern',status:'Befinden',wishes:'Wünsche',settings:'Einstellungen',credits:'Quellen und Bildrechte'};
    this.title.textContent=titles[name]??name;
    if(name==='food')this.panelBody.append(new FoodPanel(snapshot,this.room,this.drag,this.command).element);
    if(name==='social')this.panelBody.append(new SocialPanel(async(action,args)=>{this.panel.close();this.panelName='';await this.command(action,args);}).element);
    if(name==='status'){this.activePanel=new StatusPanel();this.activePanel.update(snapshot);this.panelBody.append(this.activePanel.element);}
    if(name==='wishes'){this.activePanel=new WishPanel(this.command);this.activePanel.update(snapshot);this.panelBody.append(this.activePanel.element);}
    if(name==='settings'){this.panelBody.append(new SettingsPanel(snapshot,this.command).element,button('Quellen und Bildrechte',()=>this.open('credits')),button('Paket aktualisieren',()=>{void this.command('suspend').then(()=>location.assign(new URL('./',location.href).href+'?install=1'));}));}
    if(name==='credits')this.panelBody.append(new CreditsPanel(snapshot,this.room.root).element);
    if(name==='games'){
      if(this.game)this.panel.insertBefore(this.dialogue,this.panelBody);
      else this.host.append(this.dialogue);
      if(this.game)this.panelBody.append(this.game.element);
      else for(const [id,label] of [['rock_paper_scissors','Schere–Stein–Papier'],['tic_tac_toe','Tic-Tac-Toe'],['blackjack','Blackjack'],['connect_four','Vier gewinnt'],['mastermind','Mastermind'],['quiz','Quiz']])this.panelBody.append(button(label!,()=>{void this.command('game_open',{id});}));
    }
    if(!this.panel.open)this.panel.show();
  }
  private close():void {if(this.gameId)void this.command('game_close');this.panel.close();this.panelName='';this.activePanel=undefined;}
  update(snapshot:RoomSnapshot):void {
    this.snapshot=snapshot;this.sleep.textContent=snapshot.pet.sleeping?'Aufwecken':'Schlafen';this.pet.disabled=!!snapshot.game;this.sleep.disabled=!!snapshot.game;
    const speech=snapshot.speech;this.text.textContent=speech.text;this.emote.textContent=speech.emote;this.dialogue.hidden=!speech.text&&!speech.emote;this.next.hidden=!speech.story;
    if(speech.text&&speech.id!==this.speechId&&!document.hidden){this.speechId=speech.id;requestAnimationFrame(()=>{void this.command('speech_ack',{id:speech.id});});}
    if(this.activePanel)this.activePanel.update(snapshot);
    const id=String(snapshot.game?.id??'');
    if(id!==this.gameId){
      this.game?.destroy?.();this.game=undefined;this.gameId=id;this.gameSignature='';
      const types:Record<string,()=>GameView>={rock_paper_scissors:()=>new RockPaperScissorsView(this.command,this.room.root),tic_tac_toe:()=>new TicTacToeView(this.command),blackjack:()=>new BlackjackView(this.command,this.room.root),connect_four:()=>new ConnectFourView(this.command),mastermind:()=>new MastermindView(this.command),quiz:()=>new QuizView(this.command)};
      if(id&&types[id]){this.game=types[id]!();this.open('games');}
      else {this.host.append(this.dialogue);if(this.panelName==='games')this.open('games');}
    }
    if(this.game&&snapshot.game){const signature=JSON.stringify(snapshot.game);if(signature!==this.gameSignature){this.game.update(snapshot.game);this.gameSignature=signature;}}
  }
  message(error:unknown):void {this.status.textContent=error instanceof Error?error.message:String(error);}
}
