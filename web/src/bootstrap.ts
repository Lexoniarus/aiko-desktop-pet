import './room.css';
import { BrowserRoomClient } from './platforms/browser/BrowserRoomClient';
import { BrowserLifecycle } from './platforms/browser/BrowserLifecycle';
import type { RoomReply } from './bridge/RoomClient';
import { RoomView } from './room/RoomView';
import type { AssetManifest } from './room/RoomView';
import { ObjectDragController } from './input/ObjectDragController';
import { RoomUI } from './ui/RoomUI';
import { element } from './ui/dom';
import type { Command } from './ui/dom';

export async function startRoom(host:HTMLElement,root:string):Promise<void>{
  const loading=element('p','runtime-loading','Aiko wird wach …');host.replaceChildren(loading);
  const client=new BrowserRoomClient();
  try{
    const [first,assets]=await Promise.all([client.initialize(root),fetch(new URL('runtime-assets.json',root)).then(response=>response.json() as Promise<AssetManifest>)]);
    const stage=element('section','room-stage');stage.setAttribute('aria-label','Aikos Zimmer – zum Umschauen wischen');
    host.className='aiko-room';host.replaceChildren(stage);
    const room=new RoomView(stage,root,assets);await room.initialize();
    let ui:RoomUI;let latest=0;
    const receive=async(reply:RoomReply):Promise<void>=>{
      if(!reply.snapshot||reply.requestId<latest)return;latest=reply.requestId;
      ui.update(reply.snapshot);await room.update(reply.snapshot);
    };
    const command:Command=async(name,args={})=>{
      try{await receive(await client.command(name,args));}
      catch(error){ui.message(error);}
    };
    const drag=new ObjectDragController(room,command);ui=new RoomUI(host,room,drag,command);
    room.onPetTap=()=>{void command('contact');};
    await receive(first);
    const lifecycle=new BrowserLifecycle(client,receive,error=>ui.message(error));lifecycle.start();
    window.addEventListener('pagehide',()=>drag.cancel());
  }catch(error){await client.close().catch(()=>{});throw error;}
}
