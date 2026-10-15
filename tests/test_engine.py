# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Mystical Mark Astrology contributors
# This program is free software: you can redistribute it and/or modify it under
#  the GNU Affero General Public License, version 3 or (at your option) any later version.
# Distributed WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See LICENSE for details.
# You should have received a copy of the license; if not, see https://www.gnu.org/licenses/.
import copy
from datetime import datetime,timezone
import pytest
from app.engine import *

@pytest.fixture(scope='module')
def e(tmp_path_factory):return Engine(tmp_path_factory.mktemp('ephe'),'moshier')

def test_utc_roundtrip_and_dst():
    dt=datetime(2024,4,8,18,21,tzinfo=timezone.utc)
    assert abs((from_jd(to_jd(dt))-dt).total_seconds())<.001
    with pytest.raises(ValueError):local_datetime('2024-03-10T02:30','America/New_York')
    a=local_datetime('2024-11-03T01:30','America/New_York',0);b=local_datetime('2024-11-03T01:30','America/New_York',1)
    assert (b-a).total_seconds()==3600

def test_modern_decans_and_midpoints():
    assert placement(0)['decan_ruler']=='Mars'
    assert placement(10)['decan_ruler']=='Sun'
    assert placement(20)['decan_ruler']=='Jupiter'
    assert placement(210)['decan_ruler']=='Pluto'
    assert placement(300)['decan_ruler']=='Uranus'
    assert placement(330)['decan_ruler']=='Neptune'
    assert midpoint(350,10)==0
    with pytest.raises(ValueError):midpoint(0,180)

def test_no_false_angular_root():
    assert roots(lambda x:wrap(179+2*x),0,1,step=1,angular=True)==[]
    r=roots(lambda x:(x-.3)*(x-.7),0,1,step=1,derivative=lambda x:2*x-1)
    assert r==pytest.approx([.3,.7],abs=2e-6)

def test_swiss_does_not_silently_fallback(tmp_path):
    e=Engine(tmp_path,'swiss')
    with pytest.raises(ValueError,match='fallback'):e.pos(to_jd(datetime(2024,1,1,tzinfo=timezone.utc)),'0')

def test_chart_placidus_and_polar(e):
    s=copy.deepcopy(DEFAULTS);s['houses']=True
    c=e.chart(dict(datetime='2024-04-08T12:00',timezone='America/Regina'),s)
    assert len(c['houses'])==12 and len(c['objects'])==10
    assert all(p['house'] in range(1,13) for p in c['objects'])
    assert abs(wrap(c['houses'][0]+180-c['houses'][6]))<1e-7
    polar=e.chart(dict(datetime='2024-04-08T12:00',timezone='UTC',latitude=80),s)
    assert not polar['houses'] and 'Placidus unavailable' in ' '.join(polar['warnings'])

def test_mercury_shadow_station_roots(e):
    c=next(c for c in e.retro_cycles('2',2024) if stamp(c['station_retrograde']).startswith('2024-04'))
    ps,sr,sd,pe=[c[k] for k in ('pre_shadow','station_retrograde','station_direct','post_shadow')]
    assert ps<sr<sd<pe
    assert abs(e.pos(sr,'2')['speed'])<1e-6 and abs(e.pos(sd,'2')['speed'])<1e-6
    assert e.pos(sr-.01,'2')['speed']>0>e.pos(sr+.01,'2')['speed']
    assert e.pos(sd-.01,'2')['speed']<0<e.pos(sd+.01,'2')['speed']
    assert abs(wrap(e.pos(ps,'2')['lon']-e.pos(sd,'2')['lon']))<1e-5
    assert abs(wrap(e.pos(pe,'2')['lon']-e.pos(sr,'2')['lon']))<1e-5
    # Independent published timing regression: April 1, 2024 22:14 UTC, tolerance 2 min.
    expected=to_jd(datetime(2024,4,1,22,14,tzinfo=timezone.utc))
    assert abs(sr-expected)*86400<120

def test_daily_phases_and_orb_boundaries(e):
    events=e.events('2024-04-08','UTC',copy.deepcopy(DEFAULTS))['events']
    phase=next(x for x in events if x['title']=='New Moon')
    assert abs(wrap(e.pos(phase['jd'],'1')['lon']-e.pos(phase['jd'],'0')['lon']))<2e-5
    expected=to_jd(datetime(2024,4,8,18,21,tzinfo=timezone.utc))
    assert abs(phase['jd']-expected)*86400<120
    for x in events:
        if x['kind']!='aspect':continue
        a,b=x['keys'];t=x['jd']
        assert abs(abs(wrap(e.pos(t,b)['lon']-e.pos(t,a)['lon']))-x['angle'])<2e-5
        for key in ['orb_start','orb_end']:
            if x[key] is None:continue
            j=x[key];residual=abs(abs(wrap(e.pos(j,b)['lon']-e.pos(j,a)['lon']))-x['angle'])
            assert abs(residual-x['orb'])<2e-5
        assert x['orb_start']<t<x['orb_end']

def test_midpoint_chart_exchange_symmetry(e):
    s=copy.deepcopy(DEFAULTS)
    a=e.chart(dict(name='A',datetime='1990-05-01T14:00',timezone='UTC'),s)
    b=e.chart(dict(name='B',datetime='1992-08-17T04:00',timezone='UTC'),s)
    ca=composite(a,b,s,e);cb=composite(b,a,s,e)
    assert [p['lon'] for p in ca['objects']]==pytest.approx([p['lon'] for p in cb['objects']])
    assert all(p['speed'] is None for p in ca['objects'])
