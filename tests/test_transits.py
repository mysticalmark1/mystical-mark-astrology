# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Mystical Mark Astrology contributors
# Distributed WITHOUT ANY WARRANTY. See LICENSE and NOTICE.
import copy
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo

import pytest
from app.engine import Engine,DEFAULTS,to_jd,local_datetime,wrap


def transit_spec(time='2026-04-01T12:00',tz='UTC'):
    return dict(name='Transit sky',datetime=time,timezone=tz,latitude=52,longitude=-106,fold=0)


def test_exact_moon_hit_to_fixed_natal_target(tmp_path):
    e=Engine(tmp_path,'moshier');spec=transit_spec();jd=to_jd(local_datetime(spec['datetime'],'UTC'))
    fixed=dict(e.pos(jd,'1'),key='asc',name='Ascendant')
    target=dict(name='Natal',objects=[fixed],warnings=[])
    settings={**copy.deepcopy(DEFAULTS),'objects':['1'],'aspects':[dict(name='Conjunction',glyph='☌',angle=0,orb=1,enabled=True)],'moon_aspects':False}
    result=e.transit_events(target,spec,settings)
    assert len(result['events'])==1
    hit=result['events'][0]
    assert abs(hit['jd']-jd)*86400<.2
    assert abs(wrap(e.pos(hit['jd'],'1')['lon']-fixed['lon']))<.0001
    assert hit['refs']==[dict(ring=0,key='asc'),dict(ring=1,key='1')]
    assert hit['kind']=='transit_aspect' and result['scope']=='transit_to_fixed'


def test_exact_hits_preserve_both_retrograde_passes_and_reject_wrap(tmp_path,monkeypatch):
    e=Engine(tmp_path,'moshier');spec=transit_spec();a=to_jd(local_datetime('2026-04-01T00:00','UTC'))
    # Two true conjunctions either side of a station; opposite longitude is no root.
    monkeypatch.setattr(e,'pos',lambda jd,key:dict(lon=((jd-a-.5)**2-.04)%360,speed=2*(jd-a-.5),name='Test',key=key))
    settings={**copy.deepcopy(DEFAULTS),'objects':['2'],'aspects':[dict(name='Conjunction',glyph='☌',angle=0,orb=1,enabled=True)]}
    target=dict(name='Composite',objects=[dict(lon=0,key='0',name='Sun'),dict(lon=180,key='1',name='Moon')],warnings=[])
    hits=e.transit_events(target,spec,settings)['events']
    assert len(hits)==2
    assert all(h['keys']==['0','2'] for h in hits)
    assert [round(h['jd']-a,5) for h in hits]==[.3,.7]


@pytest.mark.parametrize('day,hours',[('2026-03-08',23),('2026-11-01',25)])
def test_transit_local_day_respects_dst(tmp_path,monkeypatch,day,hours):
    e=Engine(tmp_path,'moshier');tz='America/New_York';spec=transit_spec(day+'T12:00',tz)
    start=to_jd(local_datetime(day+'T00:00',tz));seen=[]
    def pos(j,key):
        seen.append(j);return dict(lon=(j-start)*24,speed=24,name='Test',key=key)
    monkeypatch.setattr(e,'pos',pos)
    settings={**copy.deepcopy(DEFAULTS),'objects':['0'],'aspects':[dict(name='Conjunction',glyph='☌',angle=0,orb=1,enabled=True)]}
    next_day=(datetime.fromisoformat(day)+timedelta(days=1)).date().isoformat()
    end=to_jd(local_datetime(next_day+'T00:00',tz))
    # UT1 days are not exactly UTC calendar durations; anchor the end to real midnight.
    end_lon=(end-start)*24
    targets=[dict(lon=h,key=str(i),name=str(h)) for i,h in enumerate([0,end_lon-.5,end_lon])]
    hits=e.transit_events(dict(name='Natal',objects=targets,warnings=[]),spec,settings)['events']
    assert abs((max(seen)-start)*24-hours)<.001
    assert [h['keys'][0] for h in hits]==['0','1'] # Start included; next midnight excluded.
    assert all(datetime.fromisoformat(h['time']).astimezone(ZoneInfo(tz)).date().isoformat()==day for h in hits)


def test_transit_api_fixes_all_base_wheels_and_keeps_filters(monkeypatch):
    from test_api import client,headers,SPEC
    import app.main as main
    s={**copy.deepcopy(DEFAULTS),'objects':['0','1','2']}
    monkeypatch.setattr(main,'settings',lambda:copy.deepcopy(s))
    for mode,count,base_count in [('single',1,1),('composite',2,1),('synastry',6,6),('progressed',1,2)]:
        request=dict(mode=mode,charts=[{**SPEC,'name':f'Natal {i}','datetime':f'199{i}-05-01T14:00'} for i in range(count)],target='2026-04-01T12:00',transit=transit_spec())
        r=client.post('/api/chart',json=request,headers=headers);assert r.status_code==200,r.text
        a=r.json();assert len(a['charts'])==base_count+1 and a['transit_index']==base_count
        request['transit']=transit_spec('2026-04-02T12:00')
        b=client.post('/api/chart',json=request,headers=headers).json()
        assert a['charts'][:-1]==b['charts'][:-1]
        assert a['charts'][-1]['jd']!=b['charts'][-1]['jd']
        assert all(0<=x['ring_a']<x['ring_b']<=base_count for x in a['cross_aspects'])
        del request['transit']
        assert client.post('/api/chart',json=request,headers=headers).json()['charts']==a['charts'][:-1]


def test_personal_event_endpoint_for_natal_and_composite(monkeypatch):
    from test_api import client,headers,SPEC
    import app.main as main
    settings={**copy.deepcopy(DEFAULTS),'objects':['0','1'],'aspects':[dict(name='Conjunction',glyph='☌',angle=0,orb=1,enabled=True)]}
    monkeypatch.setattr(main,'settings',lambda:copy.deepcopy(settings))
    spec={**SPEC,'datetime':'2026-04-01T12:00'}
    for mode,charts in [('single',[spec]),('composite',[spec,{**spec,'datetime':'2026-04-03T12:00'}])]:
        req=dict(mode=mode,charts=charts,transit=transit_spec('2026-04-02T12:00' if mode=='composite' else '2026-04-01T12:00'))
        r=client.post('/api/transit-events',json=req,headers=headers)
        assert r.status_code==200,r.text
        assert any(e['keys']==['0','0'] for e in r.json()['events'])
        assert any(e['keys']==['1','1'] for e in r.json()['events'])
        fixed=client.post('/api/chart',json=req,headers=headers).json()['charts'][0]
        engine=main.engine('moshier')
        for hit in r.json()['events']:
            target=next(p for p in fixed['objects'] if p['key']==hit['keys'][0])
            assert abs(wrap(engine.pos(hit['jd'],hit['keys'][1])['lon']-target['lon']))<.0001
        assert client.post('/api/transit-events',json=req).status_code==403
    req['mode']='synastry'
    assert client.post('/api/transit-events',json=req,headers=headers).status_code==422
