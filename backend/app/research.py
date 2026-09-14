"""Explicit finite grid search. A matching level is not evidence of predictive value."""
from .config import Strategy
from .wheel import raw_price_angle,inverse_raw,gann_levels

def level_search(prices,reference,tolerance=1):
    if len(prices)>20 or not prices or any(p<=0 for p in prices):raise ValueError('Supply 1–20 positive reference prices')
    all_candidates=[]
    # Prespecified increments and harmonics; no fitting to the queried reference level.
    increments=[.1,.5,1,2,5,10];angles=[30,45,60,90,120,135,180,225,240,270,300,315,360]
    for price in prices:
        for mapping in ['linear','mod36','sqrt','increment','anchor']:
            for inc in increments:
                anchor=int(price//100)*100 or 1
                c=Strategy(price_mapping=mapping,increment=inc,anchor_price=anchor)
                raw=raw_price_angle(price,c)
                for angle in angles:
                    for sign in [-1,1]:
                        level=inverse_raw(raw+sign*angle,c)
                        if level is None or level<=0:continue
                        all_candidates.append({'current_price':price,'level':level,'mapping':mapping,'anchor':anchor,'increment':inc,'angle':sign*angle,
                            'cycle':None,'cycle_note':'Price-only projection; no market timestamp supplied and no time-cycle attribution possible.',
                            'distance':level-price,'reference_error':abs(level-reference),'formula':f'inverse_{mapping}(raw_price_angle({price}) + {sign*angle}); anchor={anchor}; increment={inc}; price_range=360'})
    matches=[r for r in all_candidates if r['reference_error']<=tolerance]
    return {'query':{'prices':prices,'reference':reference,'tolerance':tolerance},'grid':{'mappings':5,'increments':increments,'angles':angles,'directions':2},'tested_combinations':len(all_candidates),
            'unique_levels':len(set(round(x['level'],6) for x in all_candidates)),'matches':sorted(matches,key=lambda x:x['reference_error']),
            'conclusion':'Levels appeared within the declared grid.' if matches else 'No level matched within the declared grid and tolerance.',
            'warning':'Reference proximity is a retrospective numerical match. Equivalent formulas duplicate candidates; many tunable parameters make coincidences likely. No forecast accuracy, time relevance or historical edge is established.'}
