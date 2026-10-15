#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Mystical Mark Astrology contributors
# This program is free software: you can redistribute it and/or modify it under
#  the GNU Affero General Public License, version 3 or (at your option) any later version.
# Distributed WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See LICENSE for details.
# You should have received a copy of the license; if not, see https://www.gnu.org/licenses/.
"""Portable foreground launcher. The backend always binds to loopback."""
import argparse
import ipaddress
import os
from pathlib import Path
import sys


def data_directory():
    if os.environ.get('MM_ASTRO_DATA'):
        return Path(os.environ['MM_ASTRO_DATA']).expanduser().resolve()
    if sys.platform == 'win32':
        return Path(os.environ.get('LOCALAPPDATA', str(Path.home()/'AppData/Local')))/'MysticalMarkAstrology'
    if sys.platform == 'darwin':
        return Path.home()/'Library/Application Support/MysticalMarkAstrology'
    return Path.home()/'.local/share/mystical-mark-astrology'


def private_ipv4(value):
    try:
        addr=ipaddress.IPv4Address(value)
    except ipaddress.AddressValueError as exc:
        raise argparse.ArgumentTypeError('Use a private IPv4 address, not a URL.') from exc
    if not any(addr in ipaddress.ip_network(n) for n in ('10.0.0.0/8','172.16.0.0/12','192.168.0.0/16')):
        raise argparse.ArgumentTypeError('LAN host must be an RFC1918 private IPv4 address.')
    return str(addr)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lan-host',type=private_ipv4,help='Allow this private Host header behind Caddy; does not expose the backend.')
    parser.add_argument('--show-password',action='store_true',help='Display the existing password locally and exit.')
    args=parser.parse_args()
    os.umask(0o077)
    os.environ['MM_ASTRO_DATA']=str(data_directory())
    if args.lan_host:
        os.environ['MM_ASTRO_HOSTS']='localhost,127.0.0.1,'+args.lan_host
    from app.main import app,PASSWORD,DATA
    if args.show_password:
        print('Username: mark\nPassword: '+PASSWORD)
        return
    print(f'Data directory: {DATA}\nOpen http://127.0.0.1:8876\nUsername: mark\nUse run.py --show-password in another terminal to view your password.\nCtrl+C stops the app.',flush=True)
    import uvicorn
    uvicorn.run(app,host='127.0.0.1',port=8876,workers=1,proxy_headers=False,access_log=False)


if __name__=='__main__':main()
