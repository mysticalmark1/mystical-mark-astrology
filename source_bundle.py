# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Mystical Mark Astrology contributors
# This program is free software: you can redistribute it and/or modify it under
#  the GNU Affero General Public License, version 3 or (at your option) any later version.
# Distributed WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See LICENSE for details.
# You should have received a copy of the license; if not, see https://www.gnu.org/licenses/.
"""Package running project source, excluding runtime data and linked files."""
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT_FILES=('README.md','LICENSE','NOTICE','THIRD_PARTY_NOTICES.md','CONTRIBUTING.md','SECURITY.md','.gitignore','requirements.txt','requirements-dev.txt','install.sh','manage.py','run.py','source_bundle.py','Caddyfile.example')
TREES={'app':{'.py','.js','.css','.html'},'docs':{'.md'},'tests':{'.py','.cjs'},'.github':{'.yml','.yaml','.md'}}


def source_files(root):
    root=Path(root).resolve()
    candidates=[root/name for name in ROOT_FILES]
    for folder,suffixes in TREES.items():
        base=root/folder
        if base.is_dir() and not base.is_symlink():
            candidates.extend(p for p in base.rglob('*') if p.suffix in suffixes)
    for path in sorted(set(candidates)):
        rel=path.relative_to(root)
        if any(part in ('__pycache__','node_modules','.venv','.pytest_cache') for part in rel.parts):continue
        if any(parent.is_symlink() for parent in (path,*path.parents) if parent!=root and root in (parent,*parent.parents)):continue
        if path.is_file() and path.resolve().is_relative_to(root):yield path


def build_source_archive(root):
    root=Path(root).resolve();buffer=BytesIO()
    with ZipFile(buffer,'w',ZIP_DEFLATED) as archive:
        for path in source_files(root):archive.write(path,Path('mystical-mark-astrology')/path.relative_to(root))
    return buffer.getvalue()
