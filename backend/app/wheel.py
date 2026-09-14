"""Independent mathematical models. All directional interpretations are experimental."""
import ast
import math
import operator
from datetime import datetime,timezone
from decimal import Decimal,ROUND_HALF_UP
from zoneinfo import ZoneInfo
from .config import Strategy

def digital_root(value,decimals=0):
    d=Decimal(str(value))
    if not d.is_finite(): raise ValueError('Digital root requires finite number')
    n=int(abs(d).quantize(Decimal(1).scaleb(-decimals),rounding=ROUND_HALF_UP)*(10**decimals))
    return 0 if n==0 else 1+(n-1)%9

digitalRoot=digital_root

def normalize_angle(angle): return angle%360
def angular_distance(a,b): return abs((a-b+180)%360-180)

def safe_formula(expression,variables):
    """Arithmetic only. No names outside supplied scalar values, calls or exponentiation."""
    tree=ast.parse(expression,mode='eval')
    if len(list(ast.walk(tree)))>50: raise ValueError('Formula too complex')
    ops={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Mod:operator.mod}
    def visit(n):
        if isinstance(n,ast.Expression):return visit(n.body)
        if isinstance(n,ast.Constant) and type(n.value) in (int,float):v=n.value
        elif isinstance(n,ast.Name) and n.id in variables:v=variables[n.id]
        elif isinstance(n,ast.BinOp) and type(n.op) in ops:v=ops[type(n.op)](visit(n.left),visit(n.right))
        elif isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.UAdd,ast.USub)):v=visit(n.operand)*(1 if isinstance(n.op,ast.UAdd) else -1)
        else:raise ValueError('Only scalar arithmetic + - * / % is allowed')
        if not math.isfinite(v) or abs(v)>1e12:raise ValueError('Formula exceeds numeric limit')
        return v
    try:return visit(tree)
    except (ZeroDivisionError,OverflowError) as e:raise ValueError('Invalid formula arithmetic') from e

def local_time(ts,config):
    dt=datetime.fromtimestamp(ts,timezone.utc) if isinstance(ts,(int,float)) else ts
    if dt.tzinfo is None:raise ValueError('Timestamp must be timezone aware')
    return dt.astimezone(ZoneInfo(config.timezone))

def time_angle(ts,c:Strategy,cycle=None):
    dt=local_time(ts,c)
    if c.time_mapping=='minute_step' and cycle is None:return dt.minute*6.0
    elapsed=(dt-c.anchor_time).total_seconds() if c.anchor_time else dt.hour*3600+dt.minute*60+dt.second+dt.microsecond/1e6
    return (elapsed%(cycle or c.cycle_seconds))/(cycle or c.cycle_seconds)*360

def time_root(ts,c,price=0):
    dt=local_time(ts,c);h,m,s=dt.hour,dt.minute,dt.second
    seconds=h*3600+m*60+s
    values={'A':h+m+s,'B':int(dt.strftime('%H%M%S')),'C':seconds,'D':seconds//60,'HM24':h+m,'HM12':(h%12 or 12)+m}
    if c.time_model in values:return digital_root(values[c.time_model])
    if c.time_model=='H':return digital_root(safe_formula(c.custom_formula,{'h':h,'m':m,'s':s,'p':price,'elapsed':seconds,'date':int(dt.strftime('%Y%m%d'))}))
    return digital_root(time_angle(ts,c,{'F':43200,'G':86400}.get(c.time_model)),c.angle_decimals)

def raw_price_angle(price,c):
    if not math.isfinite(price) or price<=0:raise ValueError('Positive finite price required')
    if c.price_mapping=='linear':return price/c.price_range*360
    if c.price_mapping=='mod36':return math.floor(price/c.increment)*10
    if c.price_mapping=='sqrt':return (math.sqrt(price)-math.sqrt(c.anchor_price))*180
    if c.price_mapping=='increment':return price/c.increment*10
    return (price-c.anchor_price)/c.increment*10

def price_angle(price,c):return (c.start_angle+(1 if c.clockwise else -1)*raw_price_angle(price,c))%360

def inverse_raw(raw,c):
    if c.price_mapping=='linear':return raw/360*c.price_range
    if c.price_mapping=='sqrt':
        root=math.sqrt(c.anchor_price)+raw/180
        return root*root if root>=0 else None
    if c.price_mapping in ('mod36','increment'):return raw/10*c.increment
    return c.anchor_price+raw/10*c.increment

def wheel_levels(price,c,rings=2):
    turn=math.floor(raw_price_angle(price,c)/360)
    levels=[]
    for k in range(turn-rings,turn+rings+1):
        for sector in range(36):
            raw=k*360+sector*10;level=inverse_raw(raw,c)
            if level is not None and level>0:
                levels.append({'price':round(level,8),'angle':(c.start_angle+(1 if c.clockwise else -1)*sector*10)%360,'sector':sector+1,'root':digital_root(sector+1),'turn':k,'formula':f'inverse_{c.price_mapping}(raw={raw})'})
    return levels

def gann_levels(price):
    return [{'price':(math.sqrt(price)+sign*angle/180)**2,'source':'gann','angle':angle,'formula':f'(sqrt({price}) + {sign}*{angle}/180)^2'}
            for angle in [45,90,180,270,360] for sign in [-1,1] if math.sqrt(price)+sign*angle/180>=0]

def state(price,ts,c:Strategy):
    ta=time_angle(ts,c);pa=price_angle(price,c);directed=(pa-ta)%360
    pr=digital_root(price,c.price_decimals);tr=time_root(ts,c,price);ar=digital_root(ta,c.angle_decimals)
    dt=local_time(ts,c);dr=digital_root(int(dt.strftime('%Y%m%d')))
    matches=[{'angle':h,'distance':angular_distance(directed,h)} for h in sorted(set(x%360 for x in c.harmonics)) if angular_distance(directed,h)<=c.tolerance]
    proximity=max([1-x['distance']/c.tolerance for x in matches],default=0)
    digits=str(int(round(price*10**c.price_decimals)))
    conditions={'price_time':pr==tr,'price_angle':pr==ar,'time_angle':tr==ar,'complement':pr+tr==9,
                'sum_369':digital_root(pr+tr) in [3,6,9],'all_369':all(r in [3,6,9] for r in [pr,tr,ar]),
                'repeated_digits':any(d*3 in digits for d in '0123456789'),
                'cycle_intersection':sum(angular_distance(time_angle(ts,c,cy),0)<=c.tolerance for cy in [300,900,3600,86400])>=2,
                'angular':bool(matches)}
    triggered=[k for k in c.gates if conditions[k]]
    strength=proximity*.7+min(len(triggered),3)*.1 if matches else min(len(triggered),3)*.1
    label='VERY STRONG' if strength>=.9 else 'STRONG' if strength>=.7 else 'MODERATE' if strength>=.4 else 'WEAK' if strength>0 else 'NONE'
    sine=math.sin(math.radians(directed));tilt=0 if abs(sine)<.05 or not matches or (c.require_gate and not triggered) else (1 if sine>0 else -1)
    raw_now=raw_price_angle(price,c);display_levels=[]
    for i in range(36):
        base=(i*10-c.start_angle)*(1 if c.clockwise else -1)
        raw=base+360*round((raw_now-base)/360)
        display_levels.append({'sector':i+1,'angle':i*10,'price':inverse_raw(raw,c),'formula':f'inverse_{c.price_mapping}({raw})'})
    return {'timestamp':dt.astimezone(timezone.utc).isoformat(),'local_time':dt.isoformat(),'price':price,'time_angle':ta,'price_angle':pa,'levels':display_levels,
            'angle_difference':directed,'angular_distance':angular_distance(pa,ta),'opposite_angle':(ta+180)%360,
            'sector':int(pa//10)+1,'price_root':pr,'time_root':tr,'angle_root':ar,'date_root':dr,'harmonics':matches,
            'gate_rules':conditions,'gates':triggered,'confluence':label,'strength':strength,'numerical_direction':tilt,
            'interpretation':'Experimental sine(price angle - time angle) direction; no validated predictive edge.',
            'models':{name:time_root(ts,c.model_copy(update={'time_model':name}),price) for name in ['A','B','C','D','E','F','G','HM24','HM12']}}
