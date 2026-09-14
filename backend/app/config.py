from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo
from pydantic import BaseModel, ConfigDict, Field, model_validator

TIMEFRAMES = {'M1':60,'M5':300,'M15':900,'M30':1800,'H1':3600,'H4':14400,'D1':86400}
HARMONICS = [0,30,45,60,90,120,135,180,225,240,270,300,315,360]
GATE_RULES = ['price_time','price_angle','time_angle','complement','sum_369','all_369','repeated_digits','cycle_intersection','angular']
WEIGHTS = {'wheel':30,'geometry':20,'structure':15,'support_resistance':10,'momentum':10,'fibonacci':5,'volatility':5,'gates':5}

class Strategy(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    name: str = Field(default='Independent baseline',min_length=1,max_length=100)
    symbol: str = Field(default='XAUUSD',pattern=r'^[A-Za-z0-9._-]{1,32}$')
    timezone: str = 'UTC'
    cycle_seconds: int = Field(default=86400,ge=1,le=31557600)
    time_mapping: Literal['continuous','minute_step'] = 'continuous'
    time_model: Literal['A','B','C','D','E','F','G','H','HM24','HM12'] = 'A'
    custom_formula: str = Field(default='h + m',max_length=120)
    anchor_time: datetime | None = None
    price_mapping: Literal['linear','mod36','sqrt','increment','anchor'] = 'anchor'
    anchor_price: float = Field(default=4400,gt=0,le=1e8)
    increment: float = Field(default=1,gt=0,le=1e6)
    price_range: float = Field(default=360,gt=0,le=1e8)
    clockwise: bool = True
    start_angle: float = Field(default=0,ge=-360,le=360)
    price_decimals: int = Field(default=2,ge=0,le=6)
    angle_decimals: int = Field(default=0,ge=0,le=4)
    tolerance: float = Field(default=5,gt=0,le=30)
    harmonics: list[float] = Field(default_factory=lambda:HARMONICS.copy(),max_length=20)
    gates: list[str] = Field(default_factory=lambda:['price_time','all_369','angular'],max_length=20)
    require_gate: bool = False
    enable_369: bool = True
    enable_gann: bool = False
    weights: dict[str,float] = Field(default_factory=lambda:WEIGHTS.copy())
    threshold: float = Field(default=55,ge=0,le=100)
    ema_fast: int = Field(default=12,ge=2,le=100)
    ema_slow: int = Field(default=26,ge=3,le=150)
    sma_period: int = Field(default=20,ge=2,le=150)
    indicator_period: int = Field(default=14,ge=2,le=50)
    bb_period: int = Field(default=20,ge=2,le=100)
    bb_std: float = Field(default=2,gt=0,le=5)
    indicators: list[str] = Field(default_factory=lambda:['EMA','SMA','RSI','ADX','ATR','MACD','BB'])
    swing_strength: int = Field(default=3,ge=1,le=20)
    fib_low: float | None = Field(default=None,gt=0)
    fib_high: float | None = Field(default=None,gt=0)
    fib_direction: Literal['up','down'] = 'up'
    fib_anchor_time: datetime | None = None
    max_hold_bars: int = Field(default=30,ge=1,le=1440)
    spread: float = Field(default=0.3,ge=0,le=100)
    slippage: float = Field(default=0.05,ge=0,le=100)
    fee: float = Field(default=0,ge=0,le=100)
    initial_equity: float = Field(default=10000,gt=0)
    @model_validator(mode='after')
    def validate_all(self):
        ZoneInfo(self.timezone)
        if self.anchor_time and self.anchor_time.tzinfo is None: raise ValueError('anchor_time must include timezone')
        if self.fib_anchor_time and self.fib_anchor_time.tzinfo is None: raise ValueError('fib_anchor_time must include timezone')
        if set(self.weights)!=set(WEIGHTS) or any(v<0 or v>100 for v in self.weights.values()) or sum(self.weights.values())<=0:
            raise ValueError('All eight weights required; nonnegative and positive total')
        if any(h<0 or h>360 for h in self.harmonics): raise ValueError('Harmonics must be 0..360')
        if not set(self.gates)<=set(GATE_RULES): raise ValueError('Unknown digital gate rule')
        if not set(self.indicators)<=set(['EMA','SMA','RSI','ADX','ATR','MACD','BB']): raise ValueError('Unknown indicator')
        if (self.fib_low is None)!=(self.fib_high is None): raise ValueError('Both manual Fibonacci anchors required')
        if self.fib_low is not None and (self.fib_low>=self.fib_high or not self.fib_anchor_time): raise ValueError('Manual Fibonacci requires low < high and known-at timestamp')
        if self.ema_fast>=self.ema_slow: raise ValueError('Fast EMA must be shorter than slow EMA')
        return self

class FeedSettings(BaseModel):
    model_config=ConfigDict(extra='forbid')
    symbol:str=Field(default='XAUUSD',pattern=r'^[A-Za-z0-9._-]{1,32}$')
    terminal_path:str|None=None
    broker_utc_offset:str='+00:00'
    auto_connect:bool=False
    offset_evidence:str=Field(default='No broker offset confirmed; MT5 UTC convention used.',max_length=1000)
    @model_validator(mode='after')
    def validate_offset(self):
        from .time_normalization import offset_seconds
        offset_seconds(self.broker_utc_offset)
        return self

class ExecutionSettings(BaseModel):
    """Operational controls only; never part of the strategy/version payload."""
    model_config=ConfigDict(extra='forbid')
    selected_timeframes:list[Literal['M1','M5','M15','M30','H1','H4','D1']]=Field(default_factory=lambda:['M15'],min_length=1)
    fixed_lot:float=Field(default=.01,gt=0,le=100)
    max_trades_per_day:int|None=Field(default=3,ge=1,le=1000)
    max_positions:int|None=Field(default=1,ge=1,le=10)
    max_positions_per_timeframe:int|None=Field(default=1,ge=1,le=3)
    allow_opposite_direction:bool=False
    # External/manual XAUUSD positions are never system-owned.  By default they
    # conservatively block new entries without being counted as owned exposure.
    external_positions_block:bool=True
    cooldown_minutes:int|None=Field(default=None,ge=1,le=1440)
    maximum_spread:float|None=Field(default=None,gt=0,le=1000)
    duplicate_signal_protection:bool=True
    one_trade_per_unique_signal:bool=True
    stop_loss_mode:Literal['strategy_invalidation']='strategy_invalidation'
    take_profit_mode:Literal['strategy_target_1']='strategy_target_1'
