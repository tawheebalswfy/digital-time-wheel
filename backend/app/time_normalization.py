"""Broker wall-clock epoch correction, independent of analysis timezone.

MT5 normally documents UTC epochs. Some broker feeds encode server wall time in
the epoch field. Correction is opt-in, persisted and auditable, never inferred
anew from every tick (which could hide genuinely stale data).
"""
import math,re
from datetime import datetime,timezone

def offset_seconds(value:str)->int:
    match=re.fullmatch(r'([+-])(\d{2}):(\d{2})',value)
    if not match:raise ValueError('Broker UTC offset must be ±HH:MM')
    sign,hours,minutes=match.groups();hours=int(hours);minutes=int(minutes)
    if hours>14 or minutes>59 or (hours==14 and minutes):raise ValueError('Broker offset outside supported range')
    return (hours*3600+minutes*60)*(1 if sign=='+' else -1)

def offset_label(seconds:int)->str:
    sign='+' if seconds>=0 else '-';seconds=abs(seconds)
    return f'{sign}{seconds//3600:02d}:{seconds%3600//60:02d}'

def normalize_broker_time(raw_timestamp:float,offset:int)->float:
    if not math.isfinite(raw_timestamp) or raw_timestamp<=0:raise ValueError('Broker timestamp must be positive and finite')
    return raw_timestamp-offset

def timestamp_audit(raw_timestamp:float,offset:int):
    normalized=normalize_broker_time(raw_timestamp,offset)
    raw_wall=datetime.fromtimestamp(raw_timestamp,timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    return {'original_broker_timestamp':raw_timestamp,'broker_time':raw_wall+offset_label(offset),'normalized_utc_timestamp':normalized,
            'normalized_utc_time':datetime.fromtimestamp(normalized,timezone.utc).isoformat(),'broker_utc_offset':offset_label(offset),'broker_utc_offset_seconds':offset,
            'normalization_rule':'normalized UTC epoch = original broker wall-clock epoch - configured broker UTC offset; applied exactly once at adapter ingress'}

def validate_not_future(normalized_timestamp:float,now:float,tolerance=120):
    if normalized_timestamp>now+tolerance:raise ValueError(f'Normalized timestamp is {normalized_timestamp-now:.1f}s ahead of UTC, beyond the {tolerance}s tolerance')
