import json
from datetime import datetime
from pathlib import Path
from analyze_demo_report import stats

data=json.loads(Path('runtime/demo_report_forensic.json').read_text())
trades=data['trades']

def replay(cooldown=0, rr_floor=None):
    kept=[]; last={}
    for t in sorted(trades,key=lambda x:x['open_time']):
        dt=datetime.strptime(t['open_time'],'%Y.%m.%d %H:%M:%S')
        k=(t['symbol'],t['direction'])
        if cooldown and k in last and (dt-last[k]).total_seconds()<cooldown: continue
        if rr_floor is not None and (t['planned_rr'] is None or t['planned_rr']<rr_floor): continue
        kept.append(t); last[k]=dt
    return kept

def row(name, items):
    s=stats(items); return {'variant':name, **s}

out=[row('baseline',trades),row('same_symbol_direction_60s',replay(cooldown=60)),row('same_symbol_direction_300s',replay(cooldown=300)),row('planned_rr_floor_0.25',replay(rr_floor=.25)),row('cluster_60s_plus_rr_0.25',replay(cooldown=60,rr_floor=.25))]
Path('runtime/demo_replay.json').write_text(json.dumps(out,indent=2))
for r in out: print(r)
