# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Mystical Mark Astrology contributors
# This program is free software: you can redistribute it and/or modify it under
#  the GNU Affero General Public License, version 3 or (at your option) any later version.
# Distributed WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See LICENSE for details.
# You should have received a copy of the license; if not, see https://www.gnu.org/licenses/.
"""Tropical apparent geocentric astrology. See docs/CALCULATIONS.md.
Copyright 2026 Mystical Mark Astrology contributors. AGPL-3.0-or-later.
"""
import math
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from functools import lru_cache
from itertools import combinations
import swisseph as swe

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
SIGN_GLYPHS = list('♈♉♊♋♌♍♎♏♐♑♒♓')
RULERS = ['Mars','Venus','Mercury','Moon','Sun','Mercury','Venus','Pluto','Jupiter','Saturn','Uranus','Neptune']
NAMES = ['Sun','Moon','Mercury','Venus','Mars','Jupiter','Saturn','Uranus','Neptune','Pluto','Mean Node','True Node','Mean Lilith','True Lilith','Earth','Chiron','Pholus','Ceres','Pallas','Juno','Vesta']
GLYPHS = ['☉','☽','☿','♀','♂','♃','♄','♅','♆','♇','☊','☊','⚸','⚸','⊕','⚷','Ph','⚳','⚴','⚵','⚶']
ASPECTS = [(0,'Conjunction','☌',8),(30,'Semisextile','⚺',2),(45,'Semisquare','∠',2),(60,'Sextile','⚹',5),(72,'Quintile','Q',2),(90,'Square','□',7),(120,'Trine','△',7),(135,'Sesquiquadrate','⚼',2),(144,'Biquintile','bQ',2),(150,'Quincunx','⚻',3),(180,'Opposition','☍',8),(360/7,'Septile','S',1),(720/7,'Biseptile','bS',1),(1080/7,'Triseptile','tS',1),(40,'Novile','N',1),(80,'Binovile','bN',1),(160,'Quadranovile','qN',1),(36,'Decile','D',1),(108,'Tridecile','tD',1),(360/11,'Undecile','U',1),(720/11,'Biundecile','bU',1),(1080/11,'Triundecile','tU',1),(1440/11,'Quadriundecile','qU',1),(1800/11,'Quinundecile','5U',1),(15,'Quattuorvigintile','15°',1),(22.5,'Semioctile','22½°',1),(67.5,'Sesquioctile','67½°',1),(112.5,'Quinsemioctile','112½°',1),(157.5,'Septsemioctile','157½°',1),(165,'Quindecile','165°',1)]
DEFAULT_ASPECTS = [dict(angle=a,name=n,glyph=g,orb=o,enabled=i<11) for i,(a,n,g,o) in enumerate(ASPECTS)]
DEFAULTS = dict(engine='moshier',objects=[str(i) for i in range(10)],aspects=DEFAULT_ASPECTS,houses=False,moon_aspects=False,timezone='America/Regina',latitude=52.1332,longitude=-106.67,location='Saskatoon',sort='time',progressed_houses='natal')

def wrap(x): return (x+180)%360-180

def placement(lon):
    lon %= 360; sign=int(lon//30); dec=int(lon%30//10)
    return dict(sign=SIGNS[sign],sign_index=sign,sign_glyph=SIGN_GLYPHS[sign],degree=lon%30,decan=dec+1,decan_ruler=RULERS[(sign+4*dec)%12])

def local_datetime(value, tz, fold=0):
    dt=datetime.fromisoformat(value)
    if dt.tzinfo is not None: return dt.astimezone(timezone.utc)
    try: zone=ZoneInfo(tz)
    except (KeyError,ValueError): raise ValueError('Unknown IANA time zone. Use a name such as America/Regina.')
    aware=dt.replace(tzinfo=zone,fold=fold)
    if aware.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)!=dt:
        raise ValueError('This local time does not exist because of a clock change. Choose another time.')
    return aware.astimezone(timezone.utc)

def to_jd(dt):
    dt=dt.astimezone(timezone.utc)
    return swe.utc_to_jd(dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second+dt.microsecond/1e6,swe.GREG_CAL)[1]

def from_jd(jd):
    y,m,d,h,mi,s=swe.jdut1_to_utc(jd,swe.GREG_CAL)
    return datetime(y,m,d,h,mi,tzinfo=timezone.utc)+timedelta(seconds=s)

def stamp(jd,tz='UTC'): return from_jd(jd).astimezone(ZoneInfo(tz)).isoformat(timespec='seconds')

def bisect(f,a,b):
    fa=f(a); fb=f(b)
    if abs(fa)<1e-12: return a
    if abs(fb)<1e-12: return b
    if fa*fb>0: raise ValueError('Root is not bracketed')
    for _ in range(55):
        c=(a+b)/2; fc=f(c)
        if b-a<0.1/86400: return c
        if fa*fc<=0: b=c
        else: a=c; fa=fc
    return (a+b)/2

def roots(f,a,b,step=0.125,derivative=None,angular=False):
    """Split intervals at speed reversals; reject angular wrap discontinuities."""
    out=[]; left=a; fl=f(a)
    while left<b:
        right=min(b,left+step); fr=f(right); points=[left,right]
        if derivative:
            dl,dr=derivative(left),derivative(right)
            if dl*dr<0: points.insert(1,bisect(derivative,left,right))
        for x,y in zip(points,points[1:]):
            fx,fy=f(x),f(y)
            if fx*fy<=0 and (not angular or abs(fx-fy)<180):
                r=bisect(f,x,y)
                if a<=r<b and (not out or abs(r-out[-1])>1/86400): out.append(r)
        left=right; fl=fr
    return out

class Engine:
    def __init__(self,path,mode):
        self.path=str(path); self.mode=mode
        self.flags=(swe.FLG_MOSEPH if mode=='moshier' else swe.FLG_SWIEPH)|swe.FLG_SPEED
        swe.set_ephe_path(self.path)

    @lru_cache(maxsize=150000)
    def pos(self,jd,key):
        swe.set_ephe_path(self.path)
        flags=self.flags
        if key.startswith('star:'):
            xx,name,ret=swe.fixstar2_ut(key[5:],jd,flags); glyph='★'
        else:
            code=int(key)
            if code==14: raise ValueError('Earth is the geocentric origin, not a geocentric chart object.')
            xx,ret=swe.calc_ut(jd,code,flags)
            name=NAMES[code] if 0<=code<len(NAMES) else swe.get_planet_name(code)
            glyph=GLYPHS[code] if 0<=code<len(GLYPHS) else '•'
        actual='swiss' if ret&swe.FLG_SWIEPH else 'moshier' if ret&swe.FLG_MOSEPH else 'analytic'
        if self.mode=='swiss' and actual=='moshier':
            raise ValueError(f'{name}: Swiss files missing for this date. Download the matching data block in Settings; fallback is disabled.')
        return dict(key=key,name=name,glyph=glyph,lon=xx[0],lat=xx[1],speed=xx[3],retrograde=xx[3]<0,engine=actual,**placement(xx[0]))

    def aspects(self,aa,bb,settings,cross=False):
        out=[]
        pairs=((a,b) for a in aa for b in bb) if cross else combinations(aa,2)
        for a,b in pairs:
            delta=wrap(b['lon']-a['lon']); sep=abs(delta)
            for asp in settings['aspects']:
                err=sep-asp['angle']
                if asp['enabled'] and abs(err)<=asp['orb']:
                    speed=(b['speed']-a['speed'])*(1 if delta>=0 else -1) if a['speed'] is not None and b['speed'] is not None else None
                    out.append(dict(a=a['key'],b=b['key'],a_name=a['name'],b_name=b['name'],name=asp['name'],glyph=asp['glyph'],angle=asp['angle'],orb=abs(err),allowance=asp['orb'],applying=err*speed<0 if speed is not None else None))
        return sorted(out,key=lambda a:a['orb'])

    def chart(self,spec,settings,jd_override=None):
        unknown_time=bool(spec.get('unknown_time',False))
        if unknown_time:
            spec=dict(spec,datetime=datetime.fromisoformat(spec['datetime']).date().isoformat()+'T12:00:00',fold=0)
            settings={**settings,'houses':False,'objects':[k for k in settings['objects'] if k not in ('asc','mc','vertex','fortune','spirit')]}
        dt=local_datetime(spec['datetime'],spec.get('timezone',settings['timezone']),spec.get('fold',0))
        jd=to_jd(dt) if jd_override is None else jd_override
        if not 1800<=from_jd(jd).year<=2399: raise ValueError('Supported chart dates: 1800–2399 CE, Gregorian calendar.')
        objects=[]; warnings=[]
        if unknown_time:warnings.append('Unknown birth time: local noon is an approximation. Houses, Ascendant, MC, Vertex, Fortune and Spirit are omitted. Positions (especially Moon), progressions and exact transit hits depend on the assumed noon time.')
        for key in settings['objects']:
            if key in ('south_node','asc','mc','vertex','fortune','spirit'): continue
            try: objects.append(self.pos(jd,key).copy())
            except (swe.Error,ValueError) as e: warnings.append(str(e))
        if 'south_node' in settings['objects']:
            try:
                p=self.pos(jd,'11').copy(); p.update(key='south_node',name='South Node (true)',glyph='☋',lon=(p['lon']+180)%360);p.update(placement(p['lon']));objects.append(p)
            except (swe.Error,ValueError) as e: warnings.append(str(e))
        houses=[]; angles={}; lat=float(spec.get('latitude',settings['latitude'])); lon=float(spec.get('longitude',settings['longitude']))
        if not -89.9<=lat<=89.9 or not -180<=lon<=180: raise ValueError('Latitude or longitude out of range.')
        need_angles=settings['houses'] or any(k in settings['objects'] for k in ['asc','mc','vertex','fortune','spirit'])
        if need_angles:
            try:
                cusps,axs=swe.houses_ex(jd,lat,lon,b'P')
                angles=dict(asc=axs[0],mc=axs[1],vertex=axs[3])
                if settings['houses']: houses=list(cusps)
                for key in ['asc','mc','vertex','fortune','spirit']:
                    if key not in settings['objects']: continue
                    if key in angles: val=angles[key]
                    else:
                        sun=self.pos(jd,'0'); moon=self.pos(jd,'1')
                        altitude=swe.azalt(jd,swe.ECL2HOR,(lon,lat,0),0,15,(sun['lon'],sun['lat'],1))[1]
                        arc=moon['lon']-sun['lon']; arc=arc if altitude>=0 else -arc
                        val=(axs[0]+(arc if key=='fortune' else -arc))%360
                    objects.append(dict(key=key,name={'asc':'Ascendant','mc':'Midheaven','vertex':'Vertex','fortune':'Part of Fortune','spirit':'Part of Spirit'}[key],glyph={'asc':'AC','mc':'MC','vertex':'Vx','fortune':'⊗','spirit':'⊙'}[key],lon=val,lat=0,speed=None,retrograde=False,engine='calculated',**placement(val)))
            except swe.Error:
                warnings.append('Placidus unavailable at this latitude/date. Houses and angle-dependent points omitted; no alternate house system used.')
        for p in objects: p['house']=house_of(p['lon'],houses)
        return dict(name=spec.get('name','Current sky'),unknown_time=unknown_time,datetime=dt.astimezone(ZoneInfo(spec.get('timezone',settings['timezone']))).isoformat(timespec='seconds') if unknown_time and jd_override is None else stamp(jd,spec.get('timezone',settings['timezone'])),jd=jd,location=spec.get('location',settings['location']),latitude=lat,longitude=lon,timezone=spec.get('timezone',settings['timezone']),objects=objects,houses=houses,angles=angles,warnings=warnings,aspects=self.aspects(objects,objects,settings),method='Tropical • geocentric • apparent • '+self.mode)

    def orb_boundary(self,t,a,b,angle,orb,direction):
        f=lambda j:abs(abs(wrap(self.pos(j,b)['lon']-self.pos(j,a)['lon']))-angle)-orb
        prev=t; maxstep=0.125 if '1' in (a,b) else 0.5
        # Limit motion to a fraction of the configured orb. This matters for
        # very narrow custom aspects and close approaches to angular cusps.
        for _ in range(200000):
            relative=abs(self.pos(prev,b)['speed']-self.pos(prev,a)['speed'])
            step=min(maxstep,max(1/86400,orb/(4*max(relative,0.0001))))
            nxt=prev+direction*step
            if abs(nxt-t)>800: return None
            if f(nxt)>0: return bisect(f,min(prev,nxt),max(prev,nxt))
            prev=nxt
        return None

    def ingresses(self,key,a,b,step=0.25):
        events=[]
        # Only boundaries near the sampled path need root searches.
        t=a
        while t<b:
            end=min(t+step,b); p=self.pos(t,key); q=self.pos(end,key)
            points=[t,end]
            if p['speed']*q['speed']<0: points.insert(1,bisect(lambda j:self.pos(j,key)['speed'],t,end))
            for x,y in zip(points,points[1:]):
                lx=self.pos(x,key)['lon']; ly=lx+wrap(self.pos(y,key)['lon']-lx)
                for k in range(math.ceil(min(lx,ly)/30),math.floor(max(lx,ly)/30)+1):
                    target=k*30%360
                    for r in roots(lambda j:wrap(self.pos(j,key)['lon']-target),x,y,step=step,angular=True):
                        after=self.pos(r+1/86400,key)
                        events.append(dict(jd=r,kind='ingress',keys=[key],title=f"{p['name']} enters {after['sign']}",longitude=target))
            t=end
        return events

    @lru_cache(maxsize=120)
    def retro_cycles(self,key,year):
        # Wide padded window captures cycles whose shadows overlap selected year.
        a=to_jd(datetime(year,1,1,tzinfo=timezone.utc)); b=to_jd(datetime(year+1,1,1,tzinfo=timezone.utc))
        speed=lambda j:self.pos(j,key)['speed']
        stations=roots(speed,a-800,b+800,step=1)
        cycles=[]
        for sr,sd in zip(stations,stations[1:]):
            if speed(sr+0.01)>=0 or speed(sd+0.01)<=0: continue
            hi=self.pos(sr,key)['lon']; lo=self.pos(sd,key)['lon']
            pre=roots(lambda j:wrap(self.pos(j,key)['lon']-lo),sr-800,sr-1e-4,step=1,angular=True)
            post=roots(lambda j:wrap(self.pos(j,key)['lon']-hi),sd+1e-4,sd+800,step=1,angular=True)
            pre=[x for x in pre if speed(x)>0]; post=[x for x in post if speed(x)>0]
            ps=pre[-1] if pre else None; pe=post[0] if post else None
            if (pe or sd)<a-2 or (ps or sr)>=b+2: continue
            phases=[]
            for label,start,end in [('Pre-shadow',ps,sr),('Retrograde',sr,sd),('Post-shadow',sd,pe)]:
                decans=set(); ingress=[]
                if start is not None and end is not None:
                    steps=max(2,math.ceil((end-start)*2))
                    for i in range(steps+1):
                        pp=self.pos(start+(end-start)*i/steps,key);decans.add((pp['sign_index'],pp['decan']))
                    ingress=self.ingresses(key,start,end,step=1)
                phases.append(dict(name=label,start=start,end=end,decans=[f'{SIGNS[s]} {d} ({RULERS[(s+4*(d-1))%12]})' for s,d in sorted(decans)],ingresses=ingress))
            cycles.append(dict(key=key,name=self.pos(sr,key)['name'],station_retrograde=sr,station_direct=sd,pre_shadow=ps,post_shadow=pe,from_position=placement(hi),to_position=placement(lo),phases=phases))
        return cycles

    def transit_events(self,target,transit,settings,transit_ring=1):
        """Exact moving-to-fixed longitude hits within one transit-local calendar day.

        Targets are the already calculated natal or midpoint-composite positions.
        Moon is included when selected, independently of the mundane timeline toggle.
        """
        tz=transit['timezone']
        instant=local_datetime(transit['datetime'],tz,transit.get('fold',0)).astimezone(ZoneInfo(tz))
        day=instant.date().isoformat()
        if not 1800<=instant.year<=2398:raise ValueError('Exact transit-hit dates: 1800–2398.')
        start=local_datetime(day+'T00:00:00',tz)
        end=local_datetime((instant.date()+timedelta(days=1)).isoformat()+'T00:00:00',tz)
        a,b=to_jd(start),to_jd(end);events=[];warnings=list(target['warnings'])
        excluded={'asc','mc','vertex','fortune','spirit'}
        if excluded.intersection(settings['objects']):
            warnings.append('Moving angles and lots are excluded from exact-hit searches; their wheel aspects remain available. Fixed natal/composite angles and lots are included as targets.')
        def position(j,key):
            if key=='south_node':
                p=self.pos(j,'11');return dict(p,key=key,name='South Node (true)',lon=(p['lon']+180)%360)
            return self.pos(j,key)
        for key in settings['objects']:
            if key in excluded:continue
            try:
                moving=position(a,key);position(b,key)
                for fixed in target['objects']:
                    for asp in settings['aspects']:
                        if not asp['enabled']:continue
                        for angle in {asp['angle'],(-asp['angle'])%360}:
                            f=lambda j:wrap(position(j,key)['lon']-fixed['lon']-angle)
                            speed=lambda j:position(j,key)['speed']
                            for r in roots(f,a,b,derivative=speed,angular=True):
                                # UT1/UTC floating-point round trips can straddle midnight
                                # by microseconds. Keep display times inside the searched day.
                                hit_dt=max(start,min(from_jd(r),end-timedelta(microseconds=1))).astimezone(ZoneInfo(tz))
                                events.append(dict(jd=r,kind='transit_aspect',keys=[fixed['key'],key],
                                    refs=[dict(ring=0,key=fixed['key']),dict(ring=transit_ring,key=key)],
                                    title=f"Transit {moving['name']} {asp['name'].lower()} {target['name']} · {fixed['name']}",
                                    angle=asp['angle'],aspect_name=asp['name'],orb=asp['orb'],
                                    time=hit_dt.isoformat(timespec='seconds'),fold=hit_dt.fold))
            except (ValueError,swe.Error) as ex:warnings.append(str(ex))
        events.sort(key=lambda e:(e['title'],e['jd']) if settings['sort']=='name' else e['jd'])
        return dict(events=events,warnings=list(dict.fromkeys(warnings)),day=day,days=1,timezone=tz,
                    target=target['name'],scope='transit_to_fixed')

    def events(self,day,tz,settings,days=1):
        start=local_datetime(day+'T00:00:00',tz); end=local_datetime((datetime.fromisoformat(day)+timedelta(days=days)).date().isoformat()+'T00:00:00',tz)
        a,b=to_jd(start),to_jd(end); events=[];warnings=[]; keys=[]
        for key in settings['objects']:
            if key in ['asc','mc','vertex','fortune','spirit','south_node']: continue
            try: self.pos(a,key);self.pos(b,key);keys.append(key)
            except (ValueError,swe.Error) as e:warnings.append(str(e))
        for key in keys:
            events+=self.ingresses(key,a,b)
            if key in ('0','1','10') or key.startswith('star:'): continue
            try:
                for cycle in self.retro_cycles(key,int(day[:4])):
                    for field,label in [('pre_shadow','pre-shadow begins'),('station_retrograde','stations retrograde'),('station_direct','stations direct'),('post_shadow','post-shadow ends')]:
                        t=cycle[field]
                        if t is not None and a<=t<b:events.append(dict(jd=t,kind=field,keys=[key],title=f"{cycle['name']} {label}"))
            except (ValueError,swe.Error) as e: warnings.append(str(e))
        for p,q in combinations(keys,2):
            if '1' in (p,q) and not settings['moon_aspects']:continue
            for asp in settings['aspects']:
                if not asp['enabled']:continue
                for angle in {asp['angle'],(-asp['angle'])%360}:
                    f=lambda j:wrap(self.pos(j,q)['lon']-self.pos(j,p)['lon']-angle)
                    d=lambda j:self.pos(j,q)['speed']-self.pos(j,p)['speed']
                    for r in roots(f,a,b,derivative=d,angular=True):
                        # Sun-Moon quadratures are represented by phases below.
                        if {p,q}=={'0','1'} and asp['angle'] in (0,90,180):continue
                        before=self.orb_boundary(r,p,q,asp['angle'],asp['orb'],-1);after=self.orb_boundary(r,p,q,asp['angle'],asp['orb'],1)
                        events.append(dict(jd=r,kind='aspect',keys=[p,q],title=f"{self.pos(r,p)['name']} {asp['name'].lower()} {self.pos(r,q)['name']}",angle=asp['angle'],orb=asp['orb'],orb_start=before,orb_end=after))
        # Major lunar phases always calculated, even when Moon is hidden on wheel.
        for angle,label in [(0,'New Moon'),(90,'First Quarter Moon'),(180,'Full Moon'),(270,'Last Quarter Moon')]:
            for r in roots(lambda j:wrap(self.pos(j,'1')['lon']-self.pos(j,'0')['lon']-angle),a,b,angular=True):events.append(dict(jd=r,kind='phase',keys=['0','1'],title=label,angle=min(angle,360-angle)))
        for e in events:
            e['time']=stamp(e['jd'],tz)
            for field in ['orb_start','orb_end']:
                if field in e:e[field+'_time']=stamp(e[field],tz) if e[field] is not None else None
        events.sort(key=lambda e:(e['title'],e['jd']) if settings['sort']=='name' else e['jd'])
        return dict(events=events,warnings=list(dict.fromkeys(warnings)),timezone=tz,day=day,days=days)

def house_of(lon,cusps):
    for i,c in enumerate(cusps):
        if (lon-c)%360 < (cusps[(i+1)%12]-c)%360:return i+1
    return None

def midpoint(a,b):
    if abs(abs(wrap(b-a))-180)<1e-8:raise ValueError('An exact 180° pair has two equally near midpoints; no unique short-arc composite exists.')
    return (a+wrap(b-a)/2)%360

def composite(a,b,settings,engine):
    objects=[]; other={p['key']:p for p in b['objects']}
    for p in a['objects']:
        if p['key'] not in other:continue
        lon=midpoint(p['lon'],other[p['key']]['lon']); objects.append(dict(p,lon=lon,lat=None,speed=None,retrograde=False,engine='midpoint',**placement(lon)))
    houses=[]; warnings=a['warnings']+b['warnings']
    if a['houses'] and b['houses']:
        houses=[midpoint(x,y) for x,y in zip(a['houses'],b['houses'])]
        if abs(sum((houses[(i+1)%12]-houses[i])%360 for i in range(12))-360)>1e-5:
            houses=[];warnings.append('Midpoint cusps are not in zodiacal order. Composite houses omitted rather than silently flipping cusps.')
    for p in objects:p['house']=house_of(p['lon'],houses)
    return dict(name=f"{a['name']} + {b['name']}",unknown_time=a.get('unknown_time',False) or b.get('unknown_time',False),datetime='Midpoint composite',objects=objects,houses=houses,angles={},warnings=warnings,aspects=engine.aspects(objects,objects,settings),method='Short-arc ecliptic midpoint composite • '+('noon-based source; houses omitted' if a.get('unknown_time') or b.get('unknown_time') else 'cusps derived from natal Placidus'),location='Derived from two natal charts',timezone=a['timezone'],sources=[a,b])
