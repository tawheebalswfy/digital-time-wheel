import asyncio,json,os,threading,uuid,logging
from contextlib import asynccontextmanager
from datetime import datetime,timezone
from pathlib import Path
from fastapi import FastAPI,HTTPException,Request,WebSocket,WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse,FileResponse
from pydantic import BaseModel,Field
from .config import Strategy,FeedSettings,ExecutionSettings,TIMEFRAMES
from .database import Database,digest
from .data import parse_csv,FeedError
from .service import Service
from .backtest import run_backtest,walk_forward
from .research import level_search

ROOT=Path(__file__).resolve().parents[2]
db=Database(os.getenv('TIME_WHEEL_DB',str(ROOT/'runtime'/'timewheel.sqlite3')))
service=Service(db);jobs={};job_lock=threading.Lock()
logger=logging.getLogger('uvicorn.error')
connections={'active':0,'opened':0,'closed':0,'max_active':0,'collector_errors':0}
socket_clients={}
registered_sockets=set()
ORIGINS=['http://localhost:5173','http://127.0.0.1:5173','http://localhost:3000','http://127.0.0.1:3000','http://localhost:8000','http://127.0.0.1:8000']

@asynccontextmanager
async def lifespan(app):
    stop=asyncio.Event()
    try:await asyncio.to_thread(service.restore_feed)
    except (FeedError,ValueError):logger.exception('Saved MT5 connection could not be restored; user can reconnect from Market Data')
    async def collect():
        while not stop.is_set():
            if service.provider=='MT5':
                try:await asyncio.to_thread(service.poll)
                except Exception:
                    connections['collector_errors']+=1
                    logger.exception('Market collector failed; keeping backend alive for diagnostics')
            try:await asyncio.wait_for(stop.wait(),timeout=2)
            except asyncio.TimeoutError:pass
    task=asyncio.create_task(collect())
    yield
    stop.set();await task;service.disconnect()

app=FastAPI(title='DIGITAL TIME WHEEL XAU',version='1.0.0',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=ORIGINS,allow_methods=['GET','POST','PUT'],allow_headers=['Content-Type'])
app.add_middleware(TrustedHostMiddleware,allowed_hosts=['localhost','127.0.0.1','testserver'])

@app.middleware('http')
async def local_origin(request:Request,call_next):
    if request.method not in ['GET','HEAD','OPTIONS'] and request.headers.get('origin') and request.headers['origin'] not in ORIGINS:
        return JSONResponse({'detail':'Local application origins only'},status_code=403)
    return await call_next(request)

@app.exception_handler(ValueError)
async def value_error(request,e):return JSONResponse({'detail':str(e)},status_code=422)
@app.exception_handler(FeedError)
async def feed_error(request,e):return JSONResponse({'detail':str(e)},status_code=503)

@app.get('/api/health')
def health():return {'status':'ok','provider':service.provider,'engine_version':'1.0.0','trading_enabled':service.execution.enabled,'pid':os.getpid(),'connections':{**connections,'identified_clients':len(socket_clients)},'mt5':service.mt5.diagnostics(),'execution':service.execution.status()}
@app.get('/api/execution/status')
def execution_status():return service.execution.status()
@app.get('/api/execution/settings')
def execution_settings():return service.execution.settings.model_dump()
@app.put('/api/execution/settings')
def update_execution_settings(settings:ExecutionSettings):return service.execution.save_settings(settings)
@app.get('/api/execution/logs')
def execution_logs(limit:int=100):return db.execution_orders(min(max(limit,1),500))
@app.post('/api/execution/enable')
def execution_enable():return service.execution.enable()
@app.post('/api/execution/stop')
def execution_stop():return service.execution.stop()
@app.post('/api/execution/preview')
def execution_preview():
    tf=service.execution.settings.selected_timeframes[0];snap=service.snapshot(tf);signal=snap.get('analysis')
    if not signal:raise ValueError('No current execution-timeframe strategy signal')
    return service.execution.preview(signal)
@app.get('/api/config')
def config():return {'version':service.version,'config':service.config.model_dump(mode='json'),'timeframes':TIMEFRAMES}
@app.put('/api/config')
def update_config(c:Strategy):
    from .wheel import safe_formula
    if c.time_model=='H':safe_formula(c.custom_formula,{'h':12,'m':30,'s':15,'p':4400,'elapsed':45015,'date':20260101})
    return service.configure(c)

class Connection(BaseModel):
    symbol:str=Field(default='XAUUSD',pattern=r'^[A-Za-z0-9._-]{1,32}$')
    terminal_path:str|None=None
    timestamp_offset_seconds:int|None=Field(default=None,ge=-50400,le=50400)
@app.post('/api/feed/connect')
def connect(body:Connection):return service.connect(body.symbol,body.terminal_path,body.timestamp_offset_seconds)
@app.get('/api/mt5/symbols')
def symbols(q:str=''):
    if service.provider!='MT5': raise HTTPException(503,'MT5 is not connected')
    try:return {'symbols':service.mt5.discover_symbols(q)}
    except FeedError as e: raise HTTPException(503,str(e))
@app.post('/api/feed/disconnect')
def disconnect():
    service.set_feed_settings(service.feed_settings.model_copy(update={'auto_connect':False}));service.disconnect();return {'status':'disconnected'}
@app.get('/api/feed/settings')
def feed_settings():return service.feed_settings.model_dump()
@app.put('/api/feed/settings')
def update_feed_settings(settings:FeedSettings):return service.set_feed_settings(settings)
@app.get('/api/snapshot')
def snapshot(timeframe:str='M1'):return service.snapshot(timeframe)
@app.get('/api/datasets')
def datasets():return db.datasets()

@app.post('/api/datasets/csv')
async def import_csv(request:Request,timeframe:str='M1',symbol:str='XAUUSD',source_timezone:str='UTC'):
    content=bytearray()
    async for chunk in request.stream():
        content.extend(chunk)
        if len(content)>32*1024*1024:raise HTTPException(413,'CSV exceeds 32MB limit')
    bars=parse_csv(bytes(content),timeframe,source_timezone)
    Strategy(symbol=symbol)
    if bars[-1]['time']+TIMEFRAMES[timeframe]>datetime.now(timezone.utc).timestamp():raise ValueError('Historical imports must contain only closed bars, no future timestamps')
    meta={'symbol':symbol,'timeframe':timeframe,'source':'CSV upload','source_timezone':source_timezone,'bars':len(bars),'start':bars[0]['time'],'end':bars[-1]['time']+TIMEFRAMES[timeframe],'content_hash':digest(bars),'tick_volume_available':b'tick_volume' in content.splitlines()[0]}
    did=await asyncio.to_thread(db.save_dataset,meta,bars);return {'id':did,**meta}

@app.post('/api/datasets/{did}/select')
def select_dataset(did:str):return service.select_dataset(did)

class HistoryRequest(BaseModel):
    timeframe:str='M1'
    start:datetime
    end:datetime
@app.post('/api/datasets/mt5')
def history(body:HistoryRequest):
    if body.start.tzinfo is None or body.end.tzinfo is None or body.start>=body.end:raise ValueError('Ordered timezone-aware start/end required')
    end=min(body.end,datetime.now(timezone.utc));bars=service.mt5.get_historical_data(body.timeframe,body.start,end)
    if not bars:raise ValueError('No closed bars in requested range')
    meta={'symbol':service.mt5.symbol,'timeframe':body.timeframe,'source':'MT5','bars':len(bars),'start':bars[0]['time'],'end':bars[-1]['time']+TIMEFRAMES[body.timeframe],'content_hash':digest(bars),'timestamp_offset_seconds':service.mt5.timestamp_offset_seconds}
    return {'id':db.save_dataset(meta,bars),**meta}

@app.get('/api/signals')
def signals(limit:int=200):return db.signals(min(max(limit,1),2000))
@app.get('/api/audit')
def audit():return db.verify()

class BacktestRequest(BaseModel):
    dataset_id:str
    strategy:Strategy|None=None
    split_fraction:float=Field(default=.7,ge=.5,le=.9)
class ExperimentRequest(BaseModel):
    dataset_id:str
    strategies:list[Strategy]=Field(min_length=1,max_length=12)
    train_size:int=Field(default=1000,ge=200)
    test_size:int=Field(default=500,ge=100)

def submit_job(kind,fn):
    with job_lock:
        if any(v['status']=='running' for v in jobs.values()):raise HTTPException(409,'A research run is already in progress')
        jid=str(uuid.uuid4());jobs[jid]={'id':jid,'status':'running','kind':kind}
    def worker():
        try:
            result=fn();rid=db.save_run(kind,result)
            with job_lock:jobs[jid]={'id':jid,'status':'complete','kind':kind,'result_id':rid,'result':result}
        except Exception as e:
            with job_lock:jobs[jid]={'id':jid,'status':'failed','kind':kind,'error':str(e)}
    threading.Thread(target=worker,daemon=True).start();return {'job_id':jid,'status':'running'}

@app.post('/api/backtests')
def backtest(body:BacktestRequest):
    bars=db.bars(body.dataset_id);meta=next((r for r in db.datasets() if r['id']==body.dataset_id),None)
    if not meta:raise ValueError('Dataset not found')
    c=body.strategy or service.config
    if c.symbol!=meta['symbol']:raise ValueError('Strategy symbol must match dataset symbol')
    def run():
        split=int(len(bars)*body.split_fraction);purge=c.max_hold_bars+1
        train=run_backtest(bars,c,meta['timeframe'],end_index=split-purge)
        test=run_backtest(bars,c,meta['timeframe'],start_index=split)
        return {'dataset':meta,'dataset_id':body.dataset_id,'split_index':split,'purge_bars':purge,'train':train,'test':test,'note':'Single frozen configuration; train/test split does not itself perform optimization.'}
    return submit_job('backtests',run)

@app.post('/api/experiments')
def experiment(body:ExperimentRequest):
    bars=db.bars(body.dataset_id);meta=next((r for r in db.datasets() if r['id']==body.dataset_id),None)
    if not meta:raise ValueError('Dataset not found')
    if any(c.symbol!=meta['symbol'] for c in body.strategies):raise ValueError('All strategy symbols must match dataset')
    return submit_job('experiments',lambda:{'dataset':meta,'dataset_id':body.dataset_id,**walk_forward(bars,body.strategies,meta['timeframe'],body.train_size,body.test_size)})

@app.get('/api/jobs/{jid}')
def job(jid:str):
    with job_lock:
        if jid not in jobs:raise HTTPException(404,'Run not found; completed runs are persisted in history')
        return jobs[jid]
@app.get('/api/backtests')
def backtests():return db.runs('backtests')
@app.get('/api/experiments')
def experiments():return db.runs('experiments')

class LevelRequest(BaseModel):
    prices:list[float]=Field(min_length=1,max_length=20)
    reference:float=Field(gt=0)
    tolerance:float=Field(default=1,ge=0,le=10)
@app.post('/api/research/levels')
def levels(body:LevelRequest):return level_search(body.prices,body.reference,body.tolerance)

@app.get('/api/docs/{name}')
def document(name:str):
    if name not in ['VIDEO_REVERSE_ENGINEERING_REPORT.md','TIME_WHEEL_RESEARCH.md','VALIDATION_REPORT.md']:raise HTTPException(404)
    path=ROOT/'docs'/name
    if not path.exists():raise HTTPException(404)
    return FileResponse(path,media_type='text/markdown')

@app.websocket('/ws')
async def websocket(ws:WebSocket):
    if ws.headers.get('origin') and ws.headers['origin'] not in ORIGINS:await ws.close(code=1008);return
    await ws.accept();tf=ws.query_params.get('timeframe','M1')
    if tf not in TIMEFRAMES:await ws.close(code=1008);return
    client_id=ws.query_params.get('client_id')
    if client_id:
        if len(client_id)>100:await ws.close(code=1008);return
        previous=socket_clients.get(client_id)
        if previous:
            registered_sockets.discard(id(previous)); connections['active']=max(0,connections['active']-1)
            try:await previous.close(code=4001,reason='Replaced by the same browser tab')
            except RuntimeError:pass
        socket_clients[client_id]=ws
    registered_sockets.add(id(ws)); connections['active']+=1;connections['opened']+=1;connections['max_active']=max(connections['max_active'],connections['active'])
    async def send_updates():
        while True:
            await ws.send_json(service.snapshot(tf))
            await asyncio.sleep(2)
    async def receive_close():
        while True:
            message=await ws.receive()
            if message['type']=='websocket.disconnect':
                nonlocal registered
                if registered and id(ws) in registered_sockets:
                    registered=False; registered_sockets.discard(id(ws)); connections['active']=max(0,connections['active']-1); connections['closed']+=1
                if client_id and socket_clients.get(client_id) is ws: socket_clients.pop(client_id,None)
                return
    sender=asyncio.create_task(send_updates());receiver=asyncio.create_task(receive_close());registered=True
    try:
        done,_=await asyncio.wait([sender,receiver],return_when=asyncio.FIRST_COMPLETED)
        for task in done:task.result()
    except (WebSocketDisconnect,RuntimeError,asyncio.CancelledError):pass
    finally:
        try: await ws.close()
        except Exception: pass
        sender.cancel();receiver.cancel()
        await asyncio.gather(sender,receiver,return_exceptions=True)
        if registered and id(ws) in registered_sockets:
            registered=False
            registered_sockets.discard(id(ws))
            connections['active']=max(0,connections['active']-1);connections['closed']+=1
        if client_id and socket_clients.get(client_id) is ws:socket_clients.pop(client_id,None)
        # TestClient and some ASGI servers can cancel a receive task after the
        # transport is gone without delivering a final disconnect event. Keep
        # diagnostics fail-closed when no identified client remains.
        if not socket_clients and not client_id: connections['active']=0
        if client_id and socket_clients.get(client_id) is not ws and client_id not in socket_clients: connections['active']=0
