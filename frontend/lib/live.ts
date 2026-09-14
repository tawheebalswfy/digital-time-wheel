import {WS} from './api';
type Handlers={data:(value:Record<string,any>)=>void;status:(value:string)=>void};
type SocketLike=Pick<WebSocket,'onopen'|'onmessage'|'onerror'|'onclose'|'close'|'readyState'>;
const clientId=typeof sessionStorage==='undefined'?'test':(sessionStorage.getItem('timewheel.client')||crypto.randomUUID());
if(typeof sessionStorage!=='undefined')sessionStorage.setItem('timewheel.client',clientId);
/** One owner, one pending retry. Attempts reset only after a valid server message. */
export class LiveConnection {
 private socket:SocketLike|null=null;
 private timer:ReturnType<typeof setTimeout>|null=null;
 private generation=0;
 private attempts=0;
 constructor(private makeSocket:(url:string)=>SocketLike=(url)=>new WebSocket(url)){}
 connect(timeframe:string,handlers:Handlers){
  this.stop();const generation=this.generation;this.attempts=0;
  const open=()=>{
   if(generation!==this.generation)return;
   this.timer=null;
   const socket=this.makeSocket(`${WS}?timeframe=${encodeURIComponent(timeframe)}&client_id=${clientId}`);this.socket=socket;
   socket.onopen=()=>{if(generation===this.generation)handlers.status('CONNECTED')};
   socket.onmessage=e=>{if(generation!==this.generation||socket!==this.socket)return;try{const data=JSON.parse(String(e.data));this.attempts=0;handlers.status('CONNECTED');handlers.data(data)}catch{handlers.status('INVALID RESPONSE')}};
   socket.onerror=()=>{if(generation===this.generation)handlers.status('RECONNECTING')};
   socket.onclose=e=>{if(generation!==this.generation||socket!==this.socket)return;this.socket=null;if(e.code===4001){handlers.status('REPLACED');return}handlers.status('RECONNECTING');const delay=Math.min(30000,1000*2**Math.min(this.attempts++,5));this.timer=setTimeout(open,delay)};
  };
  open();return()=>{if(generation===this.generation)this.stop()};
 }
 stop(){this.generation++;if(this.timer!==null)clearTimeout(this.timer);this.timer=null;const socket=this.socket;this.socket=null;if(socket){socket.onopen=null;socket.onmessage=null;socket.onerror=null;socket.onclose=null;if(socket.readyState<2)socket.close()}}
}
export const liveConnection=new LiveConnection();
if(import.meta.hot)import.meta.hot.dispose(()=>liveConnection.stop());
