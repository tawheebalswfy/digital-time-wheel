"""SQLite append-only records with DB-enforced immutability and verifiable hash chain."""
import hashlib,json,sqlite3,threading,uuid
from datetime import datetime,timezone
from pathlib import Path

def canonical(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(obj):return hashlib.sha256(canonical(obj).encode()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()

class Database:
    def __init__(self,path):
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock();self.conn=sqlite3.connect(str(path),check_same_thread=False)
        self.conn.row_factory=sqlite3.Row
        self.conn.executescript('''PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;
        CREATE TABLE IF NOT EXISTS strategies(id TEXT PRIMARY KEY,name TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS strategy_versions(id TEXT PRIMARY KEY,strategy_id TEXT NOT NULL REFERENCES strategies(id),created_at TEXT NOT NULL,payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY CHECK(id=1),version_id TEXT NOT NULL REFERENCES strategy_versions(id));
        CREATE TABLE IF NOT EXISTS feed_settings(id INTEGER PRIMARY KEY CHECK(id=1),payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS execution_settings(id INTEGER PRIMARY KEY CHECK(id=1),payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS symbol_profiles(symbol TEXT PRIMARY KEY,strategy_payload TEXT NOT NULL,execution_payload TEXT NOT NULL,feed_payload TEXT NOT NULL,updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS signals(seq INTEGER PRIMARY KEY,id TEXT UNIQUE NOT NULL,event_key TEXT UNIQUE NOT NULL,created_at TEXT NOT NULL,payload TEXT NOT NULL,previous_hash TEXT NOT NULL,hash TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS signal_results(id TEXT PRIMARY KEY,signal_id TEXT NOT NULL REFERENCES signals(id),horizon INTEGER NOT NULL,payload TEXT NOT NULL,UNIQUE(signal_id,horizon));
        CREATE TABLE IF NOT EXISTS wheel_states(signal_id TEXT PRIMARY KEY REFERENCES signals(id),payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS datasets(id TEXT PRIMARY KEY,created_at TEXT NOT NULL,payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS candles(dataset_id TEXT NOT NULL REFERENCES datasets(id),time INTEGER NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(dataset_id,time));
        CREATE TABLE IF NOT EXISTS market_ticks(source TEXT NOT NULL,symbol TEXT NOT NULL,time_msc INTEGER NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(source,symbol,time_msc));
        CREATE TABLE IF NOT EXISTS backtests(id TEXT PRIMARY KEY,created_at TEXT NOT NULL,payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS experiments(id TEXT PRIMARY KEY,created_at TEXT NOT NULL,payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS execution_orders(id TEXT PRIMARY KEY,signal_id TEXT UNIQUE NOT NULL REFERENCES signals(id),created_at TEXT NOT NULL,sent_at TEXT,state TEXT NOT NULL,request_payload TEXT NOT NULL,result_payload TEXT,close_payload TEXT,updated_at TEXT NOT NULL);
        ''')
        cols={r[1] for r in self.conn.execute('PRAGMA table_info(execution_orders)')}
        if 'position_ticket' not in cols:self.conn.execute('ALTER TABLE execution_orders ADD COLUMN position_ticket INTEGER')
        if 'symbol' not in cols:self.conn.execute('ALTER TABLE execution_orders ADD COLUMN symbol TEXT')
        if 'timeframe' not in cols:self.conn.execute('ALTER TABLE execution_orders ADD COLUMN timeframe TEXT')
        self.conn.execute("UPDATE execution_orders SET symbol=COALESCE(json_extract(request_payload,'$.symbol'),json_extract(request_payload,'$.request.symbol')) WHERE symbol IS NULL")
        self.conn.execute("UPDATE execution_orders SET timeframe=COALESCE(json_extract(request_payload,'$.timeframe'),json_extract(request_payload,'$.request.timeframe')) WHERE timeframe IS NULL")
        self.conn.execute('CREATE INDEX IF NOT EXISTS idx_execution_orders_symbol ON execution_orders(symbol)')
        self.conn.execute('CREATE INDEX IF NOT EXISTS idx_execution_orders_symbol_timeframe ON execution_orders(symbol,timeframe)')
        for table in ['signals','signal_results','wheel_states','strategy_versions','candles','datasets','market_ticks','backtests','experiments']:
            for action in ['UPDATE','DELETE']:
                self.conn.execute(f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_{action} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT,'immutable record'); END")
        self.conn.commit()

    def version(self,config):
        payload=config.model_dump(mode='json');vid=digest({'engine_version':'1.0.0','config':payload})
        with self.lock,self.conn:
            sid=digest({'name':config.name})
            self.conn.execute('INSERT OR IGNORE INTO strategies VALUES(?,?,?)',(sid,config.name,now()))
            self.conn.execute('INSERT OR IGNORE INTO strategy_versions VALUES(?,?,?,?)',(vid,sid,now(),canonical(payload)))
            self.conn.execute('INSERT INTO settings VALUES(1,?) ON CONFLICT(id) DO UPDATE SET version_id=excluded.version_id',(vid,))
        return vid

    def config(self):
        with self.lock:
            r=self.conn.execute('SELECT payload FROM strategy_versions JOIN settings ON strategy_versions.id=settings.version_id').fetchone()
        return json.loads(r[0]) if r else None

    def feed_config(self):
        with self.lock:r=self.conn.execute('SELECT payload FROM feed_settings WHERE id=1').fetchone()
        return json.loads(r[0]) if r else None

    def save_feed_config(self,payload):
        with self.lock,self.conn:self.conn.execute('INSERT INTO feed_settings VALUES(1,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload',(canonical(payload),))
    def execution_config(self):
        with self.lock:r=self.conn.execute('SELECT payload FROM execution_settings WHERE id=1').fetchone()
        return json.loads(r[0]) if r else None
    def save_execution_config(self,payload):
        with self.lock,self.conn:self.conn.execute('INSERT INTO execution_settings VALUES(1,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload',(canonical(payload),))
    def symbol_profile(self,symbol):
        with self.lock:r=self.conn.execute('SELECT * FROM symbol_profiles WHERE symbol=?',(symbol,)).fetchone()
        return {'symbol':r['symbol'],'strategy':json.loads(r['strategy_payload']),'execution':json.loads(r['execution_payload']),'feed':json.loads(r['feed_payload'])} if r else None
    def save_symbol_profile(self,symbol,strategy,execution,feed):
        with self.lock,self.conn:self.conn.execute('INSERT INTO symbol_profiles VALUES(?,?,?,?,?) ON CONFLICT(symbol) DO UPDATE SET strategy_payload=excluded.strategy_payload,execution_payload=excluded.execution_payload,feed_payload=excluded.feed_payload,updated_at=excluded.updated_at',(symbol,canonical(strategy),canonical(execution),canonical(feed),now()))

    def log_signal(self,payload,key):
        with self.lock,self.conn:
            old=self.conn.execute('SELECT id FROM signals WHERE event_key=?',(key,)).fetchone()
            if old:return old[0]
            last=self.conn.execute('SELECT hash FROM signals ORDER BY seq DESC LIMIT 1').fetchone()
            previous=last[0] if last else '0'*64
            scope=f"{payload.get('symbol','UNKNOWN')}-{payload.get('timeframe','UNKNOWN')}"
            sid=f"{scope}-{uuid.uuid4()}";created=now();encoded=canonical(payload)
            h=digest({'id':sid,'event_key':key,'created_at':created,'payload':payload,'previous_hash':previous})
            self.conn.execute('INSERT INTO signals(id,event_key,created_at,payload,previous_hash,hash) VALUES(?,?,?,?,?,?)',(sid,key,created,encoded,previous,h))
            self.conn.execute('INSERT INTO wheel_states VALUES(?,?)',(sid,canonical(payload['wheel'])))
            return sid

    def signals(self,limit=200):
        with self.lock:
            rows=self.conn.execute('SELECT * FROM signals ORDER BY seq DESC LIMIT ?',(limit,)).fetchall()
            return [{**dict(r),'payload':json.loads(r['payload']),'results':[json.loads(x[0]) for x in self.conn.execute('SELECT payload FROM signal_results WHERE signal_id=?',(r['id'],))]} for r in rows]

    def verify(self):
        previous='0'*64;count=0
        with self.lock:
            for r in self.conn.execute('SELECT * FROM signals ORDER BY seq'):
                h=digest({'id':r['id'],'event_key':r['event_key'],'created_at':r['created_at'],'payload':json.loads(r['payload']),'previous_hash':previous})
                if r['previous_hash']!=previous or r['hash']!=h:return {'valid':False,'count':count,'failed_id':r['id']}
                previous=h;count+=1
        return {'valid':True,'count':count,'head_hash':previous,'scope':'Local hash-chain integrity; external tamper-proof anchoring is not provided.'}

    def save_result(self,sid,horizon,payload):
        with self.lock,self.conn:self.conn.execute('INSERT OR IGNORE INTO signal_results VALUES(?,?,?,?)',(digest([sid,horizon]),sid,horizon,canonical(payload)))

    def save_dataset(self,metadata,bars):
        did=digest({'metadata':metadata,'bars':bars})
        with self.lock,self.conn:
            self.conn.execute('INSERT OR IGNORE INTO datasets VALUES(?,?,?)',(did,now(),canonical(metadata)))
            self.conn.executemany('INSERT OR IGNORE INTO candles VALUES(?,?,?)',[(did,b['time'],canonical(b)) for b in bars])
        return did

    def datasets(self):
        with self.lock:return [{'id':r['id'],**json.loads(r['payload'])} for r in self.conn.execute('SELECT * FROM datasets ORDER BY created_at DESC')]

    def bars(self,did):
        with self.lock:return [json.loads(r[0]) for r in self.conn.execute('SELECT payload FROM candles WHERE dataset_id=? ORDER BY time',(did,))]

    def save_tick(self,source,symbol,tick):
        with self.lock,self.conn:self.conn.execute('INSERT OR IGNORE INTO market_ticks VALUES(?,?,?,?)',(source,symbol,tick['time_msc'],canonical(tick)))

    def save_run(self,kind,payload):
        if kind not in ['backtests','experiments']:raise ValueError('Invalid run table')
        rid=str(uuid.uuid4())
        with self.lock,self.conn:self.conn.execute(f'INSERT INTO {kind} VALUES(?,?,?)',(rid,now(),canonical(payload)))
        return rid

    def runs(self,kind):
        if kind not in ['backtests','experiments']:raise ValueError('Invalid run table')
        with self.lock:return [{'id':r['id'],'created_at':r['created_at'],**json.loads(r['payload'])} for r in self.conn.execute(f'SELECT * FROM {kind} ORDER BY created_at DESC LIMIT 50')]

    # Execution records deliberately live outside the immutable research ledger: their
    # lifecycle must be updated when MT5 reports a fill or a later close.  The original
    # signal remains immutable and signal_id has a UNIQUE constraint for restart-safe dedupe.
    def reserve_execution(self,signal_id,request,symbol=None,timeframe=None):
        eid=str(uuid.uuid4());created=now()
        with self.lock,self.conn:
            symbol=symbol or request.get('symbol') or request.get('request',{}).get('symbol'); timeframe=timeframe or request.get('timeframe') or request.get('request',{}).get('timeframe')
            cur=self.conn.execute('INSERT OR IGNORE INTO execution_orders(id,signal_id,created_at,sent_at,state,request_payload,result_payload,close_payload,updated_at,symbol,timeframe) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(eid,signal_id,created,None,'ORDER_PENDING',canonical(request),None,None,created,symbol,timeframe))
            return eid if cur.rowcount else None
    def mark_execution_sent(self,eid,result,state='EXECUTION_ERROR',sent=True):
        with self.lock,self.conn:self.conn.execute('UPDATE execution_orders SET sent_at=CASE WHEN ? THEN ? ELSE sent_at END,state=?,result_payload=?,updated_at=? WHERE id=?',(sent,now(),state,canonical(result),now(),eid))
    def close_execution(self,eid,close):
        with self.lock,self.conn:self.conn.execute('UPDATE execution_orders SET state=?,close_payload=?,updated_at=? WHERE id=?',('CLOSED',canonical(close),now(),eid))
    def set_position_ticket(self,eid,ticket):
        with self.lock,self.conn:self.conn.execute('UPDATE execution_orders SET position_ticket=?,updated_at=? WHERE id=?',(int(ticket),now(),eid))
    def execution_orders(self,limit=100,symbol=None,timeframe=None,status=None):
        filters=[];params=[]
        if symbol:filters.append('symbol=?');params.append(symbol)
        if timeframe:filters.append('timeframe=?');params.append(timeframe)
        if status:filters.append('state=?');params.append(status)
        clause=(' WHERE '+' AND '.join(filters)) if filters else ''
        with self.lock:rows=self.conn.execute('SELECT * FROM execution_orders'+clause+' ORDER BY created_at DESC LIMIT ?',(*params,limit)).fetchall()
        return [{**dict(r),'request':json.loads(r['request_payload']),'result':json.loads(r['result_payload']) if r['result_payload'] else None,'close':json.loads(r['close_payload']) if r['close_payload'] else None} for r in rows]
    def daily_sent_count(self,symbol=None):
        with self.lock:return self.conn.execute("SELECT count(*) FROM execution_orders WHERE sent_at IS NOT NULL AND date(sent_at)=date('now')"+(' AND symbol=?' if symbol else ''),((symbol,) if symbol else ())).fetchone()[0]
