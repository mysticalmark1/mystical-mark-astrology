# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Mystical Mark Astrology contributors
# This program is free software: you can redistribute it and/or modify it under
#  the GNU Affero General Public License, version 3 or (at your option) any later version.
# Distributed WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See LICENSE for details.
# You should have received a copy of the license; if not, see https://www.gnu.org/licenses/.
import os,tempfile
os.environ['MM_ASTRO_DATA']=tempfile.mkdtemp(prefix='mm-test-')
from fastapi.testclient import TestClient
from app.main import app,PASSWORD
client=TestClient(app,base_url='http://127.0.0.1')
client.auth=('mark',PASSWORD)
headers={'X-MM-Request':'1'}
SPEC=dict(name='Test client',datetime='1990-05-01T14:00',timezone='UTC',latitude=52.1332,longitude=-106.67)

def test_access_and_csrf():
    unauth=TestClient(app,base_url='http://127.0.0.1')
    assert unauth.get('/api/meta').status_code==401
    assert client.get('/api/meta',headers={'Host':'evil.example'}).status_code==403
    assert client.post('/api/charts',json=SPEC).status_code==403
    assert client.post('/api/charts',json=SPEC,headers={**headers,'Origin':'https://evil.example'}).status_code==403
    r=client.get('/');assert r.status_code==200 and "frame-ancestors 'none'" in r.headers['content-security-policy']

def test_chart_storage_backup_restore():
    r=client.post('/api/charts',json=SPEC,headers=headers);assert r.status_code==200
    ident=r.json()['id'];assert any(c['id']==ident for c in client.get('/api/charts').json())
    backup=client.get('/api/backup').json();count=len(client.get('/api/charts').json())
    r=client.post('/api/restore',json=backup,headers=headers);assert r.status_code==200
    assert len(client.get('/api/charts').json())==count+len(backup['charts'])
    assert client.put('/api/charts/'+ident,json={**SPEC,'name':'Edited'},headers=headers).status_code==200
    assert client.delete('/api/charts/'+ident,headers=headers).status_code==200

def test_chart_modes_and_progressed_epoch():
    for mode,specs in [('single',[SPEC]),('synastry',[SPEC,{**SPEC,'datetime':'1995-01-01T00:00'}]),('composite',[SPEC,{**SPEC,'datetime':'1995-01-01T00:00'}]),('progressed',[SPEC])]:
        r=client.post('/api/chart',json=dict(mode=mode,charts=specs,target='2020-05-01T14:00'),headers=headers)
        assert r.status_code==200,r.text
        assert r.json()['charts'][0]['objects']
        if mode=='progressed':
            a,b=r.json()['charts'];assert 29.99<b['jd']-a['jd']<30.01
        if mode=='synastry':assert r.json()['cross_aspects']

def test_reject_malformed_data():
    assert client.post('/api/ephemeris/download',json={'block':99},headers=headers).status_code==422
    assert client.post('/api/ephemeris/import',json={'filename':'../../bad','content':'AA=='},headers=headers).status_code==422
    assert client.post('/api/restore',json={'schema':99},headers=headers).status_code==422
    assert client.get('/api/events?day=2024-01-01&days=1000').status_code==422

def test_source_and_license_offer():
    from io import BytesIO
    from zipfile import ZipFile
    unauth=TestClient(app,base_url='http://127.0.0.1')
    for path in ('/api/license','/api/source'):
        assert unauth.get(path).status_code==401
    license=client.get('/api/license')
    assert license.status_code==200 and 'GNU AFFERO GENERAL PUBLIC LICENSE' in license.text
    source=client.get('/api/source')
    assert source.status_code==200 and source.headers['content-type']=='application/zip'
    with ZipFile(BytesIO(source.content)) as archive:
        assert 'mystical-mark-astrology/run.py' in archive.namelist()
        assert all('access-password' not in name and not name.endswith('.sqlite3') for name in archive.namelist())
    page=client.get('/').text
    assert 'href="/api/source"' in page and 'href="/api/license"' in page
