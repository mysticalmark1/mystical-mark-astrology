#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Mystical Mark Astrology contributors
# This program is free software: you can redistribute it and/or modify it under
#  the GNU Affero General Public License, version 3 or (at your option) any later version.
# Distributed WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See LICENSE for details.
# You should have received a copy of the license; if not, see https://www.gnu.org/licenses/.
"""Install/inspect a separate Caddy gateway; does not edit other applications' gateways."""
import argparse, ipaddress, os, secrets, shutil, subprocess, sys
from pathlib import Path
HOME=Path.home();DATA=HOME/'.local/share/mystical-mark-astrology';CONFIG=HOME/'.config/mystical-mark-astrology'

def command(*args):subprocess.run(args,check=True)
def lan(ip,cidrs):
    caddy=shutil.which('caddy')
    if not caddy:raise SystemExit('Install Caddy first: sudo pacman -S --needed caddy')
    address=ipaddress.IPv4Address(ip)
    private=[ipaddress.ip_network(x) for x in ['10.0.0.0/8','172.16.0.0/12','192.168.0.0/16']]
    if not any(address in n for n in private):raise SystemExit('Gateway address must be RFC1918 LAN/VPN IPv4.')
    networks=[ipaddress.IPv4Network(n,strict=True) for n in cidrs.split(',')]
    if not networks or not all(any(n.subnet_of(p) for p in private) for n in networks):raise SystemExit('Allowlist must contain only RFC1918 subnet CIDRs.')
    CONFIG.mkdir(parents=True,exist_ok=True,mode=0o700)
    caddyfile=CONFIG/'Caddyfile'
    # This user service shares the user's existing Caddy local CA, but no admin port.
    content='''{
    admin off
    auto_https disable_redirects
    skip_install_trust
    storage file_system {
        root "CA_PATH"
    }
}
https://ADDRESS:9444 {
    bind ADDRESS
    tls internal
    @allowed remote_ip CIDRS
    handle @allowed {
        reverse_proxy 127.0.0.1:8876
    }
    handle {
        respond "Private LAN / VPN access only" 403
    }
}
'''.replace('CA_PATH',str(HOME/'.local/share/caddy')).replace('ADDRESS',str(address)).replace('CIDRS',' '.join(map(str,networks)))
    pending=CONFIG/'Caddyfile.pending';pending.write_text(content)
    command(caddy,'validate','--config',str(pending),'--adapter','caddyfile')
    pending.replace(caddyfile)
    (CONFIG/'environment').write_text('MM_ASTRO_HOSTS=localhost,127.0.0.1,'+str(address)+'\n')
    unit=HOME/'.config/systemd/user/mystical-mark-astrology-gateway.service'
    unit.parent.mkdir(parents=True,exist_ok=True)
    unit.write_text(f'''[Unit]
Description=Mystical Mark Astrology private HTTPS gateway
After=network-online.target mystical-mark-astrology.service
Wants=network-online.target
[Service]
ExecStart={caddy} run --config {caddyfile} --adapter caddyfile
Restart=on-failure
RestartSec=5
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
[Install]
WantedBy=default.target
''')
    command('systemctl','--user','daemon-reload')
    command('systemctl','--user','restart','mystical-mark-astrology.service')
    command('systemctl','--user','enable','--now','mystical-mark-astrology-gateway.service')
    print(f'Phone / VPN URL: https://{address}:9444\nOther applications retain their existing configurations.\nCaddy CA: {HOME}/.local/share/caddy/pki/authorities/local/root.crt\nAllow only your chosen private subnets to TCP 9444 in your existing firewall. No router port forwarding.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['password','reset-password','lan','status']);parser.add_argument('--ip',help='Private LAN IPv4 address; required for lan');parser.add_argument('--cidrs',help='Comma-separated private LAN/VPN CIDRs; required for lan');args=parser.parse_args()
    if args.command in ['password','reset-password']:
        DATA.mkdir(parents=True,exist_ok=True,mode=0o700);p=DATA/'access-password'
        if args.command=='reset-password' or not p.exists():p.write_text(secrets.token_urlsafe(24));p.chmod(0o600)
        print('Username: mark\nPassword: '+p.read_text().strip())
        if args.command=='reset-password':command('systemctl','--user','restart','mystical-mark-astrology.service')
    elif args.command=='lan':
        if not args.ip or not args.cidrs:parser.error('lan requires --ip and --cidrs; see README.md')
        lan(args.ip,args.cidrs)
    else:command('systemctl','--user','status','mystical-mark-astrology.service','mystical-mark-astrology-gateway.service','--no-pager')
