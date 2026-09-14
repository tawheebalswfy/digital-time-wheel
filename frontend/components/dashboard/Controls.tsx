'use client';
import {Select,SelectContent,SelectItem,SelectTrigger,SelectValue} from '@/components/ui/select';
import {Checkbox} from '@/components/ui/checkbox';
import {Input} from '@/components/ui/input';
export function Choice({label,value,options,onChange}:{label:string,value:string,options:any[],onChange:(v:string)=>void}){return <label className="field">{label}<Select value={value} onValueChange={v=>v!==null&&onChange(String(v))}><SelectTrigger aria-label={label} style={{width:'100%'}}><SelectValue>{options.map(x=>Array.isArray(x)?x:[x,x]).find(x=>x[0]===value)?.[1]||value||'Choose…'}</SelectValue></SelectTrigger><SelectContent>{options.map(x=>{const[v,l]=Array.isArray(x)?x:[x,x];return <SelectItem key={v} value={v}>{l}</SelectItem>})}</SelectContent></Select></label>}
export function Check({label,checked,onChange}:{label:string,checked:boolean,onChange:(v:boolean)=>void}){return <label className="check-row"><Checkbox checked={checked} onCheckedChange={onChange}/>{label}</label>}
export function Field({label,value,onChange,type='number',step='any'}:{label:string,value:any,onChange:(v:any)=>void,type?:string,step?:string}){return <label className="field">{label}<Input type={type} step={step} value={value??''} onChange={e=>onChange(type==='number'?(e.target.value===''?'':Number(e.target.value)):e.target.value)}/></label>}
export function download(name:string,value:unknown){const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
export const fmt=(v:unknown,d=2)=>typeof v==='number'&&Number.isFinite(v)?v.toLocaleString('en-US',{maximumFractionDigits:d,minimumFractionDigits:d}):'—';
export const date=(v:number)=>new Date(v*1000).toISOString().replace('T',' ').slice(0,19)+' UTC';
