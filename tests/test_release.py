# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Mystical Mark Astrology contributors
# This program is free software: you can redistribute it and/or modify it under
#  the GNU Affero General Public License, version 3 or (at your option) any later version.
# Distributed WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See LICENSE for details.
# You should have received a copy of the license; if not, see https://www.gnu.org/licenses/.
"""Release privacy, source completeness and portable startup regression checks."""
import argparse
from io import BytesIO
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import pytest
import run
from source_bundle import build_source_archive, source_files

ROOT=Path(__file__).resolve().parents[1]


def test_source_archive_excludes_runtime_and_symlinks(tmp_path):
    for name in ('README.md','run.py','app/main.py','docs/guide.md',
                 'access-password','charts.sqlite3','.env','Caddyfile.local',
                 'app/private.key','app/__pycache__/secret.py','ephe/data.se1',
                 '.venv/lib/site.py','data/client.json'):
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('fixture')
    (tmp_path/'app/linked.py').symlink_to(tmp_path/'access-password')
    (tmp_path/'app/linked-folder').symlink_to(tmp_path/'data',target_is_directory=True)
    (tmp_path/'data/secret.py').write_text('secret')
    with ZipFile(BytesIO(build_source_archive(tmp_path))) as z:
        names={n.removeprefix('mystical-mark-astrology/') for n in z.namelist()}
    assert names=={'README.md','run.py','app/main.py','docs/guide.md'}


def test_source_release_contains_runnable_project():
    names={str(p.relative_to(ROOT)) for p in source_files(ROOT)}
    assert {'LICENSE','NOTICE','README.md','requirements.txt','install.sh','run.py',
            'manage.py','source_bundle.py','app/main.py','app/engine.py',
            'app/static/index.html','.gitignore','docs/HTTPS.md',
            'docs/PUBLISHING.md','THIRD_PARTY_NOTICES.md'} <= names
    # Every source file required by the installer must exist and be distributed.
    import re
    copy_line=next(line for line in (ROOT/'install.sh').read_text().splitlines() if line.startswith('cp -R '))
    for name in re.findall(r'\$source_dir/([^"\s]+)',copy_line):
        assert (ROOT/name).exists()
        assert name in names or any(p.startswith(name+'/') for p in names)


@pytest.mark.parametrize('platform,suffix',[
    ('win32','MysticalMarkAstrology'),
    ('darwin','Library/Application Support/MysticalMarkAstrology'),
    ('linux','.local/share/mystical-mark-astrology'),
])
def test_portable_data_paths(monkeypatch,tmp_path,platform,suffix):
    monkeypatch.delenv('MM_ASTRO_DATA',raising=False)
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path))
    monkeypatch.setattr(run.sys,'platform',platform)
    monkeypatch.setattr(run.Path,'home',lambda:tmp_path)
    assert run.data_directory()==tmp_path/suffix
    monkeypatch.setenv('MM_ASTRO_DATA',str(tmp_path/'custom'))
    assert run.data_directory()==tmp_path/'custom'


def test_lan_address_validation():
    for address in ('10.1.2.3','172.16.1.2','192.168.1.50'):
        assert run.private_ipv4(address)==address
    for address in ('8.8.8.8','127.0.0.1','0.0.0.0','169.254.1.1','https://192.168.1.1','localhost'):
        with pytest.raises(argparse.ArgumentTypeError):run.private_ipv4(address)


def test_foreground_launcher_keeps_loopback(monkeypatch,tmp_path,capsys):
    import types
    calls=[]
    monkeypatch.setitem(sys.modules,'app.main',types.SimpleNamespace(app=object(),PASSWORD='fixture-secret',DATA=tmp_path))
    monkeypatch.setitem(sys.modules,'uvicorn',types.SimpleNamespace(run=lambda *a,**kw:calls.append(kw)))
    monkeypatch.setattr(sys,'argv',['run.py','--lan-host','192.168.1.50'])
    monkeypatch.setenv('MM_ASTRO_DATA',str(tmp_path))
    monkeypatch.setenv('MM_ASTRO_HOSTS','localhost,127.0.0.1')
    run.main()
    assert calls==[dict(host='127.0.0.1',port=8876,workers=1,proxy_headers=False,access_log=False)]
    assert 'fixture-secret' not in capsys.readouterr().out


def test_password_command_preserves_generated_password(tmp_path):
    import os
    env={**os.environ,'MM_ASTRO_DATA':str(tmp_path)}
    result=subprocess.run([sys.executable,'run.py','--show-password'],cwd=ROOT,env=env,capture_output=True,text=True,check=True)
    password=(tmp_path/'access-password').read_text().strip()
    assert len(password)>=24 and 'Password: '+password in result.stdout
    again=subprocess.run([sys.executable,'run.py','--show-password'],cwd=ROOT,env=env,capture_output=True,text=True,check=True)
    assert again.stdout==result.stdout
