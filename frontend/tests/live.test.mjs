import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import ts from 'typescript';
// Compile the production class; only inject the browser-specific URL module.
const source=(await readFile(new URL('../lib/live.ts',import.meta.url),'utf8')).replace("import {WS} from './api';","const WS='ws://127.0.0.1:8000/ws';");
const compiled=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022}}).outputText;
const {LiveConnection}=await import('data:text/javascript;base64,'+Buffer.from(compiled).toString('base64'));
const originalSet=globalThis.setTimeout,originalClear=globalThis.clearTimeout;
let timers=new Map(),counter=0,sockets=[],states=[],messages=[];
globalThis.setTimeout=(fn,delay)=>{const id=++counter;timers.set(id,{fn,delay});return id};
globalThis.clearTimeout=id=>timers.delete(id);
const factory=url=>{const socket={url,readyState:0,closeCount:0,close(){this.closeCount++;this.readyState=3},onopen:null,onclose:null,onerror:null,onmessage:null};sockets.push(socket);return socket};
const handlers={status:x=>states.push(x),data:x=>messages.push(x)};
const fail=()=>{const s=sockets.at(-1);s.readyState=3;s.onclose({code:1006})};
const retry=expected=>{assert.equal(timers.size,1);const [id,timer]=[...timers][0];assert.equal(timer.delay,expected);timers.delete(id);timer.fn()};
try{
 const live=new LiveConnection(factory);
 const oldCleanup=live.connect('M1',handlers);assert.equal(sockets.length,1);
 const staleMessage=sockets[0].onmessage;
 live.connect('H1',handlers);assert.equal(sockets[0].closeCount,1);oldCleanup();assert.equal(sockets[1].closeCount,0);
 staleMessage({data:'{"stale":true}'});assert.equal(messages.length,0);
 fail();retry(1000);fail();retry(2000);fail();retry(4000);fail();retry(8000);fail();retry(16000);fail();retry(30000);fail();retry(30000);
 sockets.at(-1).onmessage({data:'{"provider":"MT5"}'});assert.equal(messages.length,1);
 fail();retry(1000);
 const latest=sockets.at(-1);latest.readyState=3;latest.onclose({code:4001});assert.equal(timers.size,0);assert.equal(states.at(-1),'REPLACED');
 live.connect('M5',handlers);fail();assert.equal(timers.size,1);live.stop();assert.equal(timers.size,0);
 assert(sockets.every(s=>s.url.includes('client_id=')&&s.url.startsWith('ws://127.0.0.1:8000/ws?')));
 assert(sockets.filter(s=>s.readyState<2).length===0);
 console.log('PASS: single socket ownership, stale callbacks ignored, retry cancellation, exponential backoff capped at 30s, reset on valid data, duplicate session replacement, shared endpoint.');
}finally{globalThis.setTimeout=originalSet;globalThis.clearTimeout=originalClear}
