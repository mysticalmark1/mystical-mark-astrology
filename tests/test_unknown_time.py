# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Mystical Mark Astrology contributors
# Distributed WITHOUT ANY WARRANTY. See LICENSE and NOTICE.
import copy
import pytest
from app.engine import Engine,DEFAULTS,to_jd,local_datetime

POINTS={'asc','mc','vertex','fortune','spirit'}
SPEC=dict(name='Unknown example',datetime='1990-05-01T03:15',timezone='America/Regina',latitude=52.13,longitude=-106.67,unknown_time=True)
SETTINGS={**copy.deepcopy(DEFAULTS),'houses':True,'objects':['0','1','2',*sorted(POINTS)]}

def assert_no_time_points(chart):
    assert chart['unknown_time']
    assert chart['houses']==[] and chart['angles']=={}
    assert not POINTS.intersection(p['key'] for p in chart['objects'])
    assert all(p['house'] is None for p in chart['objects'])
    assert any('Unknown birth time' in w for w in chart['warnings'])

def test_unknown_time_noon_and_per_chart_isolation(tmp_path):
    e=Engine(tmp_path,'moshier');s=copy.deepcopy(SETTINGS);original=copy.deepcopy(s)
    a=e.chart(SPEC,s);assert_no_time_points(a)
    assert abs(a['jd']-to_jd(local_datetime('1990-05-01T12:00','America/Regina')))<1e-8
    known=e.chart({**SPEC,'unknown_time':False},s)
    assert len(known['houses'])==12 and POINTS.issubset(p['key'] for p in known['objects'])
    assert s==original

@pytest.mark.parametrize('house_mode',['natal','quotidian'])
def test_unknown_time_modes_and_transit_isolation(monkeypatch,house_mode):
    from test_api import client,headers
    import app.main as main
    s={**copy.deepcopy(SETTINGS),'progressed_houses':house_mode}
    monkeypatch.setattr(main,'settings',lambda:copy.deepcopy(s))
    known={**SPEC,'name':'Known example','datetime':'1992-06-02T04:10','unknown_time':False}
    transit={**known,'datetime':'2026-10-15T12:00'}
    for mode,charts in [('single',[SPEC]),('synastry',[SPEC,known]),('composite',[SPEC,known]),('progressed',[SPEC])]:
        req=dict(mode=mode,charts=charts,target='2026-10-15T12:00',transit=transit,houses=True)
        response=client.post('/api/chart',json=req,headers=headers);assert response.status_code==200,response.text
        result=response.json();assert_no_time_points(result['charts'][0])
        if mode=='progressed':assert_no_time_points(result['charts'][1])
        if mode=='synastry':assert len(result['charts'][1]['houses'])==12
        assert len(result['charts'][-1]['houses'])==12
        assert POINTS.issubset(p['key'] for p in result['charts'][-1]['objects'])
        assert not any(a['ring_a']==0 and a['a'] in POINTS for a in result['cross_aspects'])

def test_save_edit_backup_restore_unknown_time():
    from test_api import client,headers
    r=client.post('/api/charts',json=SPEC,headers=headers);assert r.status_code==200
    ident=r.json()['id']
    saved=next(c for c in client.get('/api/charts').json() if c['id']==ident)
    assert saved['unknown_time'] and saved['datetime']=='1990-05-01T12:00:00'
    backup=client.get('/api/backup').json()
    assert client.post('/api/restore',json=backup,headers=headers).status_code==200
    restored=[c for c in client.get('/api/charts').json() if c['name']==SPEC['name']]
    assert len(restored)>=2 and all(c['unknown_time'] for c in restored)
    known={**SPEC,'unknown_time':False,'datetime':'1990-05-01T07:30'}
    assert client.put('/api/charts/'+ident,json=known,headers=headers).status_code==200
    saved=next(c for c in client.get('/api/charts').json() if c['id']==ident)
    assert saved['unknown_time'] is False and saved['datetime']==known['datetime']
    from app.main import Spec
    legacy={k:v for k,v in SPEC.items() if k!='unknown_time'}
    assert Spec(**legacy).unknown_time is False
    assert Spec(**{**SPEC,'datetime':'1990-05-01'}).datetime=='1990-05-01T12:00:00'
