import math
from .wheel import state,wheel_levels,gann_levels,raw_price_angle,inverse_raw
from .technical import fibonacci,finite
from .config import Strategy

def targets(price,direction,row,w,c,ts):
    if not direction:return {'targets':[],'invalidation':None,'candidates':[]}
    atr=finite(row.get('atr'));candidates=[]
    def add(level,source,formula,**details):
        if level is not None and math.isfinite(level) and level>0 and (level-price)*direction>max(.01,atr*.2):
            candidates.append({'price':round(level,6),'source':source,'formula':formula,'distance':abs(level-price),**details})
    for item in wheel_levels(price,c,2):add(item['price'],'wheel',item['formula'],angle=item['angle'],anchor=c.anchor_price,increment=c.increment)
    raw=raw_price_angle(price,c)
    for angle in sorted(set(c.harmonics)):
        if angle:
            add(inverse_raw(raw+direction*angle,c),'angular',f'inverse_{c.price_mapping}({raw}+{direction}*{angle})',angle=angle,anchor=c.anchor_price)
    for name in ['support','resistance','swing_high','swing_low']:
        add(finite(row.get(name)),name,'previously observed '+name)
    for item in fibonacci(row,c,ts):add(item['price'],'fibonacci',item['formula'],ratio=item['ratio'])
    for multiple in [1,2,3]:add(price+direction*atr*multiple,'atr',f'{price}+{direction}*{atr}*{multiple}',multiple=multiple)
    if c.enable_gann:
        for item in gann_levels(price):add(item['price'],'gann',item['formula'],angle=item['angle'])
    if w['gates']:
        for item in wheel_levels(price,c,1):
            if item['root']==w['time_root']:add(item['price'],'digital_gate',item['formula'],rules=w['gates'])
    # Cluster candidates within a meaningful fraction of ATR, retaining every rationale.
    clusters=[]
    for item in sorted(candidates,key=lambda x:x['distance']):
        if clusters and abs(item['price']-clusters[-1]['price'])<=max(.01,atr*.1):clusters[-1]['reasons'].append(item)
        else:clusters.append({'price':item['price'],'distance':item['distance'],'reasons':[item]})
    chosen=clusters[:3]
    stop=price-direction*max(1.5*atr,c.increment)
    if stop<=0:stop=price*.5
    return {'targets':chosen,'invalidation':{'price':stop,'reason':f'Entry minus direction * max(1.5*ATR={1.5*atr:.6f}, increment={c.increment})'},'candidates':candidates}

def analyze(row,c:Strategy,ts):
    p=float(row['close']);w=state(p,ts,c);d=w['numerical_direction'];atr=finite(row.get('atr'))
    direction=lambda v:1 if v>0 else -1 if v<0 else 0
    structure={'BULLISH':1,'BEARISH':-1}.get(row.get('structure'),0)
    momentum_votes=[];enabled=c.indicators
    if 'EMA' in enabled:momentum_votes.append(direction(finite(row.get('ema_fast'))-finite(row.get('ema_slow'))))
    if 'SMA' in enabled:momentum_votes.append(direction(p-finite(row.get('sma'),p)))
    if 'RSI' in enabled:
        rsi=finite(row.get('rsi'),50);momentum_votes.append(1 if rsi>55 else -1 if rsi<45 else 0)
    if 'MACD' in enabled:momentum_votes.append(direction(finite(row.get('macd_hist'))))
    if 'ADX' in enabled and finite(row.get('adx'))>20:momentum_votes.append(direction(finite(row.get('plus_di'))-finite(row.get('minus_di'))))
    if 'BB' in enabled:momentum_votes.append(direction(p-finite(row.get('bb_mid'),p)))
    momentum=direction(sum(momentum_votes))
    support=finite(row.get('support'));resistance=finite(row.get('resistance'))
    sr=1 if support and p>support and p-support<atr*.5 else -1 if resistance and p<resistance and resistance-p<atr*.5 else 0
    fib=fibonacci(row,c,ts)
    fib_vote=structure if any(abs(p-v['price'])<atr*.3 for v in fib) else 0
    components={'wheel':d,'geometry':d,'structure':structure,'support_resistance':sr,'momentum':momentum,'fibonacci':fib_vote,
                'volatility':d if 'ATR' in enabled and .00001<atr/p<.02 else 0,'gates':d if w['gates'] else 0}
    total=sum(c.weights.values());scores={name:round(100*sum(c.weights[k] for k,v in components.items() if v==sign)/total,4) for name,sign in [('buy',1),('sell',-1),('neutral',0)]}
    winner=1 if scores['buy']>scores['sell'] else -1 if scores['sell']>scores['buy'] else 0
    confirm=any(components[k]==d for k in ['structure','support_resistance','momentum','fibonacci']) if d else False
    final=winner if winner==d and confirm and max(scores['buy'],scores['sell'])>=c.threshold else 0
    confidence=scores['buy'] if final==1 else scores['sell'] if final==-1 else scores['neutral']
    reasons=[w['interpretation'],f"Numerical confluence: {w['confluence']}; directed separation {w['angle_difference']:.3f}°",f"Structure: {row.get('structure','RANGING')} ({row.get('high_pattern','—')}/{row.get('low_pattern','—')})",f"Technical momentum vote: {momentum}; enabled indicators: {', '.join(enabled)}",f"Triggered gates: {', '.join(w['gates']) or 'none'}"]
    if not final:reasons.append('No actionable combined signal: numerical direction, technical confirmation and threshold must all agree.')
    target=targets(p,final,row,w,c,ts)
    indicators={k:finite(row.get(k),None) for k in ['ema_fast','ema_slow','sma','rsi','adx','atr','macd','macd_signal','macd_hist','bb_mid','bb_upper','bb_lower','volatility']}
    return {'timestamp':ts,'price':p,'direction':'BUY' if final==1 else 'SELL' if final==-1 else 'NEUTRAL','direction_value':final,
            'label':('STRONG ' if final and confidence>=75 else '')+('BUY' if final==1 else 'SELL' if final==-1 else 'NEUTRAL'),
            'confidence':confidence,'confidence_kind':'uncalibrated weighted evidence score, not probability','scores':scores,'numerical_signal':d,
            'technical_signal':direction(structure+momentum+sr),'components':components,'wheel':w,'reasons':reasons,'structure':row.get('structure','RANGING'),
            'momentum':momentum,'indicators':indicators,'fibonacci':fib,'support':support,'resistance':resistance,**target}
