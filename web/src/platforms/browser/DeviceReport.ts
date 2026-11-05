export function downloadDeviceReport(runtime:unknown,startedAt:number):void {
  const report={
    createdAt:new Date().toISOString(),
    target:'iPad (9. Generation), iPadOS 26.6',
    browser:navigator.userAgent,
    standalone:matchMedia('(display-mode: standalone)').matches,
    secureContext:isSecureContext,
    serviceWorker:!!navigator.serviceWorker.controller,
    online:navigator.onLine,
    startupMilliseconds:Math.round(performance.now()-startedAt),
    runtime,
    deviceAcceptance:'Nur tatsächlich durchgeführte Schritte im Abnahmeblatt bestätigen.',
  };
  const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'}));
  const link=document.createElement('a');link.href=url;link.download='aiko-geraetebericht.json';link.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
