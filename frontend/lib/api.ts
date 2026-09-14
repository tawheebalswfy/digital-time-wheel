export type Config=Record<string,any>;
export type Snapshot=Record<string,any>;
export const API=(import.meta.env.VITE_API_URL||'http://127.0.0.1:8000').replace(/\/$/,'');
export const WS=API.replace(/^http/,'ws')+'/ws';
export async function api(path:string,options:RequestInit={}){const response=await fetch(API+path,{...options,headers:{'Content-Type':'application/json',...options.headers}});if(!response.ok){const e=await response.json().catch(()=>({detail:response.statusText}));throw new Error(typeof e.detail==='string'?e.detail:JSON.stringify(e.detail))}return response.json()}
