# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Mystical Mark Astrology contributors
# This program is free software: you can redistribute it and/or modify it under
#  the GNU Affero General Public License, version 3 or (at your option) any later version.
# Distributed WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See LICENSE for details.
# You should have received a copy of the license; if not, see https://www.gnu.org/licenses/.
"""Local API. Single uvicorn worker: Swiss Ephemeris state is serialized."""
import base64, copy, hashlib, hmac, ipaddress, json, os, re, secrets, sqlite3, threading, time, urllib.request
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import swisseph as swe
from .engine import Engine,DEFAULTS,NAMES,GLYPHS,SIGNS,SIGN_GLYPHS,RULERS,local_datetime,to_jd,stamp,composite

DATA=Path(os.environ.get('MM_ASTRO_DATA',str(Path.home()/'.local/share/mystical-mark-astrology')))
DATA.mkdir(parents=True,exist_ok=True,mode=0o700)
EPHE=DATA/'ephe';EPHE.mkdir(exist_ok=True,mode=0o700)
LOCK=threading.RLock();DB=DATA/'charts.sqlite3'
SECRET=DATA/'access-password'
if not SECRET.exists():SECRET.write_text(secrets.token_urlsafe(24));SECRET.chmod(0o600)
PASSWORD=SECRET.read_text().strip()
HOSTS=set(os.environ.get('MM_ASTRO_HOSTS','localhost,127.0.0.1').split(','))
app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)

def db():
    con=sqlite3.connect(DB,timeout=20);con.row_factory=sqlite3.Row;con.execute('PRAGMA foreign_keys=ON');return con
with db() as con:
    con.execute('CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY,value TEXT NOT NULL)')
    con.execute('CREATE TABLE IF NOT EXISTS charts (id TEXT PRIMARY KEY,payload TEXT NOT NULL,updated TEXT NOT NULL)')
    con.execute("INSERT OR IGNORE INTO meta VALUES ('schema','1')")
    con.execute("INSERT OR IGNORE INTO meta VALUES ('settings',?)",(json.dumps(DEFAULTS),))
    version=con.execute("SELECT value FROM meta WHERE key='schema'").fetchone()[0]
    if version!='1':raise RuntimeError('Database version is newer than this app. Start the newer release; database has not been modified.')
os.chmod(DB,0o600)

@app.middleware('http')
async def security(request:Request,call_next):
    host=request.url.hostname
    if host not in HOSTS:return Response('Unrecognized host',status_code=403)
    if request.client and request.client.host not in ('127.0.0.1','::1','testclient'):
        return Response('Use the loopback listener behind the private Caddy gateway.',status_code=403)
    authorization=request.headers.get('authorization','')
    good=False
    if authorization.startswith('Basic '):
        try:
            user,pw=base64.b64decode(authorization[6:],validate=True).decode().split(':',1)
            good=hmac.compare_digest(user,'mark') and hmac.compare_digest(pw,PASSWORD)
        except (ValueError,UnicodeDecodeError):pass
    if not good:return Response('Sign in as mark using the password available through install.sh or run.py --show-password.',401,headers={'WWW-Authenticate':'Basic realm="Mystical Mark Astrology", charset="UTF-8"'})
    if request.method in ('POST','PUT','DELETE','PATCH'):
        if request.headers.get('x-mm-request')!='1':return Response('Missing request protection',403)
        origin=request.headers.get('origin')
        if origin and urlsplit(origin).netloc!=request.headers.get('host'):return Response('Origin mismatch',403)
        try:
            if int(request.headers.get('content-length','0'))>30_000_000:return Response('Request too large',413)
        except ValueError:return Response('Invalid request size',400)
    result=await call_next(request)
    result.headers['Cache-Control']='no-store'
    result.headers['X-Content-Type-Options']='nosniff'
    result.headers['Referrer-Policy']='no-referrer'
    result.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    return result

@app.exception_handler(ValueError)
async def value_error(req,exc):return JSONResponse({'detail':str(exc)},status_code=422)
@app.exception_handler(swe.Error)
async def swe_error(req,exc):return JSONResponse({'detail':str(exc)},status_code=422)

def settings():
    with db() as con:return json.loads(con.execute("SELECT value FROM meta WHERE key='settings'").fetchone()[0])

@lru_cache(maxsize=2)
def engine(mode):return Engine(EPHE,mode)

class Spec(BaseModel):
    name:str=Field(default='Current sky',max_length=200)
    datetime:str
    timezone:str='America/Regina'
    latitude:float=Field(default=52.1332,ge=-89.9,le=89.9)
    longitude:float=Field(default=-106.67,ge=-180,le=180)
    location:str=Field(default='Saskatoon',max_length=200)
    fold:int=Field(default=0,ge=0,le=1)
    notes:str=Field(default='',max_length=20000)

class ChartRequest(BaseModel):
    charts:list[Spec]=Field(min_length=1,max_length=6)
    mode:str='single'
    target:str|None=None
    houses:bool|None=None

@app.get('/api/meta')
def meta():return dict(version='1.2.0',swisseph=swe.version,settings=settings(),bodies=[dict(key=str(i),name=n,glyph=GLYPHS[i]) for i,n in enumerate(NAMES) if i!=14],signs=SIGNS,sign_glyphs=SIGN_GLYPHS,rulers=RULERS)

@app.post('/api/chart')
def chart(req:ChartRequest):
    s=settings()
    if req.houses is not None:s['houses']=req.houses
    if req.mode not in ('single','synastry','composite','progressed'):raise ValueError('Unknown chart mode')
    with LOCK:
        e=engine(s['engine']);specs=[p.model_dump() for p in req.charts];charts=[e.chart(p,s) for p in specs]
        if req.mode=='composite':
            if len(charts)!=2:raise ValueError('A midpoint composite requires exactly two charts.')
            charts=[composite(*charts,s,e)]
        if req.mode=='progressed':
            if len(specs)!=1 or not req.target:raise ValueError('Choose one natal chart and a target date.')
            birth=charts[0]['jd']; target=to_jd(local_datetime(req.target,specs[0]['timezone']))
            progressed=birth+(target-birth)/365.242190402
            ps=copy.deepcopy(s)
            if s.get('progressed_houses','natal')=='natal':
                ps['houses']=False;ps['objects']=[k for k in ps['objects'] if k not in ['asc','mc','vertex','fortune','spirit']]
            pc=e.chart(specs[0],ps,jd_override=progressed)
            pc['name']=specs[0]['name']+' • progressed';pc['target']=req.target
            pc['method']='Secondary day/year • 365.242190402-day year • '+('natal Placidus reference houses' if s['progressed_houses']=='natal' else 'quotidian Placidus at progressed instant')
            if s['progressed_houses']=='natal':
                from .engine import house_of
                pc['houses']=charts[0]['houses'];pc['angles']=charts[0]['angles']
                for p in pc['objects']:p['house']=house_of(p['lon'],pc['houses'])
            charts=[charts[0],pc]
        cross=[]
        if len(charts)>1:
            for i in range(len(charts)):
                for j in range(i+1,len(charts)):
                    for a in e.aspects(charts[i]['objects'],charts[j]['objects'],s,True):cross.append(dict(a,ring_a=i,ring_b=j))
        return dict(charts=charts,cross_aspects=cross,mode=req.mode)

@app.get('/api/events')
def events(day:str,tz:str='America/Regina',days:int=1):
    if not 1<=days<=31:raise ValueError('Choose 1–31 days at a time.')
    if not 1803<=int(day[:4])<=2395:raise ValueError('Event dates: 1803–2395 (padding required for shadows).')
    s=settings()
    with LOCK:return engine(s['engine']).events(day,tz,s,days)

@app.get('/api/retrogrades')
def retrogrades(year:int,keys:str='2,3,4,5,6,7,8,9',tz:str='America/Regina'):
    if not 1803<=year<=2395:raise ValueError('Retrograde years: 1803–2395.')
    result=[];warnings=[];selected=keys.split(',')
    if len(selected)>32:raise ValueError('Select up to 32 objects per retrograde search.')
    with LOCK:
        e=engine(settings()['engine'])
        for key in selected:
            if not re.fullmatch(r'\d{1,7}',key) or key in ('0','1','10','14'):continue
            try:
                for c in e.retro_cycles(key,year):
                    c=copy.deepcopy(c)
                    for field in ['station_retrograde','station_direct','pre_shadow','post_shadow']:c[field+'_time']=stamp(c[field],tz) if c[field] is not None else None
                    for phase in c['phases']:
                        phase['start_time']=stamp(phase['start'],tz) if phase['start'] else None;phase['end_time']=stamp(phase['end'],tz) if phase['end'] else None
                        for ingress in phase['ingresses']:ingress['time']=stamp(ingress['jd'],tz)
                    result.append(c)
            except (ValueError,swe.Error) as ex:warnings.append(str(ex))
    return dict(cycles=sorted(result,key=lambda c:c['station_retrograde']),warnings=warnings,timezone=tz)

@app.get('/api/charts')
def saved_charts():
    with db() as con:return [dict(id=r['id'],**json.loads(r['payload'])) for r in con.execute('SELECT * FROM charts ORDER BY updated DESC')]
@app.post('/api/charts')
def save_chart(spec:Spec):
    local_datetime(spec.datetime,spec.timezone,spec.fold)
    if not 1800<=int(spec.datetime[:4])<=2399:raise ValueError('Chart dates: 1800–2399.')
    ident=secrets.token_hex(12)
    with db() as con:con.execute('INSERT INTO charts VALUES (?,?,?)',(ident,spec.model_dump_json(),datetime.now(timezone.utc).isoformat()))
    return {'id':ident}
@app.put('/api/charts/{ident}')
def edit_chart(ident:str,spec:Spec):
    local_datetime(spec.datetime,spec.timezone,spec.fold)
    with db() as con:
        cur=con.execute('UPDATE charts SET payload=?,updated=? WHERE id=?',(spec.model_dump_json(),datetime.now(timezone.utc).isoformat(),ident))
        if cur.rowcount!=1:raise HTTPException(404,'Chart not found')
    return {'ok':True}
@app.delete('/api/charts/{ident}')
def delete_chart(ident:str):
    with db() as con:con.execute('DELETE FROM charts WHERE id=?',(ident,))
    return {'ok':True}

def validate_settings(s):
    s={**copy.deepcopy(DEFAULTS),**s}
    if s['engine'] not in ('moshier','swiss'):raise ValueError('Unknown engine')
    if s['sort'] not in ('time','name'):raise ValueError('Unknown event order')
    if s['progressed_houses'] not in ('natal','quotidian'):raise ValueError('Unknown progression house method')
    if not isinstance(s['houses'],bool) or not isinstance(s['moon_aspects'],bool):raise ValueError('Invalid toggles')
    if not 1<=len(s['objects'])<=60 or len(set(s['objects']))!=len(s['objects']):raise ValueError('Select 1–60 distinct objects.')
    for k in s['objects']:
        if not isinstance(k,str) or not (re.fullmatch(r'\d{1,7}',k) or re.fullmatch(r'star:[\w ,.+-]{1,60}',k) or k in ['south_node','asc','mc','vertex','fortune','spirit']):raise ValueError('Invalid object key')
    if not 1<=len(s['aspects'])<=80:raise ValueError('Choose 1–80 aspect definitions.')
    for a in s['aspects']:
        if not 0<=float(a['angle'])<=180 or not 0<float(a['orb'])<=15:raise ValueError('Aspect angles must be 0–180°; orbs >0–15°.')
        if not isinstance(a['enabled'],bool) or not 1<=len(a['name'])<=60 or len(a['glyph'])>10:raise ValueError('Invalid aspect definition')
        a['angle']=float(a['angle']);a['orb']=float(a['orb'])
    local_datetime('2026-01-01T12:00',s['timezone'])
    if not -89.9<=float(s['latitude'])<=89.9 or not -180<=float(s['longitude'])<=180:raise ValueError('Invalid coordinates')
    return s
@app.post('/api/settings')
def save_settings(s:dict):
    s=validate_settings(s)
    with db() as con:con.execute("UPDATE meta SET value=? WHERE key='settings'",(json.dumps(s),))
    return s

@app.get('/api/backup')
def backup():
    with db() as con:
        payload=dict(format='mystical-mark-astrology',schema=1,created=datetime.now(timezone.utc).isoformat(),settings=settings(),charts=[dict(id=r['id'],**json.loads(r['payload'])) for r in con.execute('SELECT * FROM charts')])
    return Response(json.dumps(payload,ensure_ascii=False,indent=2),media_type='application/json',headers={'Content-Disposition':'attachment; filename="mystical-mark-astrology-backup.json"'})
@app.post('/api/restore')
def restore(payload:dict):
    if payload.get('format')!='mystical-mark-astrology' or payload.get('schema')!=1:raise ValueError('Not a supported backup.')
    if len(payload.get('charts',[]))>10000:raise ValueError('Too many charts')
    specs=[Spec.model_validate(c) for c in payload.get('charts',[])]
    for spec in specs:local_datetime(spec.datetime,spec.timezone,spec.fold)
    s=validate_settings(payload['settings'])
    # Safety copy before additive import. Existing charts are never overwritten.
    target=DATA/('before-import-'+str(time.time_ns())+'.sqlite3')
    with db() as con,sqlite3.connect(target) as dest:con.backup(dest)
    target.chmod(0o600)
    with db() as con:
        for spec in specs:con.execute('INSERT INTO charts VALUES (?,?,?)',(secrets.token_hex(12),spec.model_dump_json(),datetime.now(timezone.utc).isoformat()))
        con.execute("UPDATE meta SET value=? WHERE key='settings'",(json.dumps(s),))
    return dict(imported=len(specs),message='Imported as new records; previous records preserved.')

class Download(BaseModel):
    block:int=18
@app.post('/api/ephemeris/download')
def download(req:Download):
    if req.block not in (12,18):raise ValueError('Supported blocks: 1200–1799 or 1800–2399.')
    names=[f'{prefix}_{req.block:02}.se1' for prefix in ('sepl','semo','seas')]+['sefstars.txt']
    results=[]
    with LOCK:
        for name in names:
            url='https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/'+name
            tmp=EPHE/(name+'.part')
            try:
                with urllib.request.urlopen(url,timeout=60) as response:
                    if urlsplit(response.url).hostname!='raw.githubusercontent.com':raise ValueError('Unexpected download destination')
                    total=0
                    with tmp.open('wb') as out:
                        while chunk:=response.read(65536):
                            total+=len(chunk)
                            if total>20_000_000:raise ValueError('Download exceeds expected size')
                            out.write(chunk)
                if total<100:raise ValueError('Empty or incomplete ephemeris file')
                # Swiss files contain a textual version header, then binary data.
                if name.endswith('.se1') and b'SWISSEPH' not in tmp.read_bytes()[:200].upper():raise ValueError('Not a Swiss Ephemeris data file')
                digest=hashlib.sha256(tmp.read_bytes()).hexdigest();tmp.replace(EPHE/name);(EPHE/name).chmod(0o600)
                results.append(dict(file=name,bytes=total,sha256=digest))
            except Exception as ex:
                tmp.unlink(missing_ok=True);raise ValueError(f'{name}: {ex}. Previously completed files retained; retry to finish.') from ex
        swe.close();engine.cache_clear()
    (EPHE/'download-manifest.json').write_text(json.dumps(dict(source='Astrodienst official GitHub',downloaded=datetime.now(timezone.utc).isoformat(),files=results),indent=2))
    return dict(files=results,message='Files downloaded. Select Swiss and save settings to activate.')

class EpheImport(BaseModel):
    filename:str
    content:str
@app.post('/api/ephemeris/import')
def import_ephemeris(req:EpheImport):
    # Numbered asteroid files only. Path comes from the validated file number.
    match=re.fullmatch(r'(se\d{5,6}s?\.se1|s\d{6}s?\.se1)',req.filename)
    if not match:raise ValueError('Choose an official numbered-asteroid seNNNNN[s].se1 / sNNNNNN[s].se1 file.')
    raw=base64.b64decode(req.content,validate=True)
    if not 100<len(raw)<=20_000_000 or b'SWISSEPH' not in raw[:200].upper():raise ValueError('Invalid asteroid file header or size.')
    num=int(re.search(r'\d+',req.filename).group())
    folder=EPHE/f'ast{num//1000}';folder.mkdir(exist_ok=True,mode=0o700)
    with LOCK:
        tmp=folder/(req.filename+'.part');tmp.write_bytes(raw);tmp.chmod(0o600);tmp.replace(folder/req.filename);swe.close();engine.cache_clear()
    return dict(file=req.filename,object_key=str(swe.AST_OFFSET+num))
@app.get('/api/ephemeris')
def ephemeris():return dict(files=[dict(name=str(p.relative_to(EPHE)),bytes=p.stat().st_size) for p in EPHE.rglob('*') if p.is_file()])

@app.get('/api/license')
def license_text():
    return FileResponse(Path(__file__).resolve().parent.parent/'LICENSE',media_type='text/plain')

@app.get('/api/source')
def source_download():
    from source_bundle import build_source_archive
    content=build_source_archive(Path(__file__).resolve().parent.parent)
    return Response(content,media_type='application/zip',headers={'Content-Disposition':'attachment; filename="mystical-mark-astrology-source.zip"'})

STATIC=Path(__file__).parent/'static' 
@app.get('/')
def index():return FileResponse(STATIC/'index.html')
app.mount('/static',StaticFiles(directory=STATIC),name='static')
