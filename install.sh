#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Mystical Mark Astrology contributors
# This program is free software: you can redistribute it and/or modify it under
#  the GNU Affero General Public License, version 3 or (at your option) any later version.
# Distributed WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See LICENSE for details.
# You should have received a copy of the license; if not, see https://www.gnu.org/licenses/.
set -euo pipefail
umask 077
if [[ "$(uname -s)" != Linux ]] || ! command -v systemctl >/dev/null; then
  echo "This installer requires Linux with systemd. For other systems, use run.py as documented in README.md." >&2; exit 1
fi
if [[ $(id -u) -eq 0 ]]; then echo 'Run this as your regular desktop user, not with sudo.' >&2; exit 1; fi
source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
app_root="$HOME/.local/lib/mystical-mark-astrology"
data_root="$HOME/.local/share/mystical-mark-astrology"
config_root="$HOME/.config/mystical-mark-astrology"
release="$app_root/releases/1.2.0-$(date +%Y%m%d%H%M%S)-$$"
mkdir -p "$app_root/releases" "$data_root" "$config_root" "$HOME/.config/systemd/user"
if [[ "$HOME" == *' '* || "$HOME" == *'%'* ]]; then echo 'This installer requires a home path without spaces or percent signs.' >&2; exit 1; fi
command -v python3 >/dev/null || { echo 'Install Python: sudo pacman -S --needed python python-pip base-devel'; exit 1; }
mkdir "$release"
cp -R "$source_dir/app" "$source_dir/docs" "$source_dir/requirements.txt" "$source_dir/manage.py" "$source_dir/LICENSE" "$source_dir/README.md" "$source_dir/run.py" "$source_dir/source_bundle.py" "$source_dir/install.sh" "$source_dir/NOTICE" "$source_dir/THIRD_PARTY_NOTICES.md" "$source_dir/CONTRIBUTING.md" "$source_dir/SECURITY.md" "$source_dir/Caddyfile.example" "$source_dir/requirements-dev.txt" "$source_dir/.gitignore" "$source_dir/tests" "$release/"
python3 -m venv "$release/.venv"
CC=gcc CXX=g++ "$release/.venv/bin/python" -m pip install -r "$release/requirements.txt"
# Validate the new release against temporary data before touching the current link.
check_dir=$(mktemp -d)
MM_ASTRO_DATA="$check_dir" PYTHONPATH="$release" "$release/.venv/bin/python" -c 'from app.main import app; from app.engine import Engine; import tempfile; assert len(Engine(tempfile.mkdtemp(),"moshier").chart({"datetime":"2000-01-01T12:00","timezone":"UTC"}, __import__("app.engine",fromlist=["DEFAULTS"]).DEFAULTS)["objects"]) == 10'
rm -r -- "$check_dir"
if [[ -f "$data_root/charts.sqlite3" ]]; then
  "$release/.venv/bin/python" - "$data_root" <<'PY'
import sqlite3,sys,datetime,pathlib
root=pathlib.Path(sys.argv[1]); backup=root/('before-update-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.sqlite3')
with sqlite3.connect(root/'charts.sqlite3') as src, sqlite3.connect(backup) as dst: src.backup(dst)
print('Database backup created before update.')
PY
fi
old_release=$(readlink "$app_root/current" || true)
if [[ -n "$old_release" ]]; then ln -sfn "$old_release" "$app_root/previous"; fi
ln -s "$release" "$app_root/current.new"
mv -Tf "$app_root/current.new" "$app_root/current"
cat > "$HOME/.config/systemd/user/mystical-mark-astrology.service" <<EOF
[Unit]
Description=Mystical Mark Astrology (private loopback backend)
After=network.target
[Service]
Type=simple
WorkingDirectory=$app_root/current
Environment=MM_ASTRO_DATA=$data_root
EnvironmentFile=-$config_root/environment
ExecStart=$app_root/current/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8876 --workers 1 --no-proxy-headers --no-access-log
Restart=on-failure
RestartSec=4
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$data_root
[Install]
WantedBy=default.target
EOF
"$release/.venv/bin/python" "$release/manage.py" password
systemctl --user daemon-reload
systemctl --user enable mystical-mark-astrology.service
systemctl --user restart mystical-mark-astrology.service
printf '\nOpen http://127.0.0.1:8876 (username: mark).\n'
printf 'For optional phone/VPN HTTPS access, supply your own network values:\n%s\n' "\"$app_root/current/.venv/bin/python\" \"$app_root/current/manage.py\" lan --ip YOUR_PRIVATE_IP --cidrs YOUR_PRIVATE_SUBNET"
printf 'For startup before desktop login: sudo loginctl enable-linger "%s"\n' "$USER"
