# Contributing

Issues and pull requests are welcome once this project is published on GitHub. Explain the problem, expected behavior and a reproducible example. Use fictional chart data; do not post clients' birth details, notes, backups, passwords or certificate keys.

For calculation changes, state the astronomical convention and supply a primary reference and a focused regression test. Preserve explicit missing-data errors and avoid silent engine or house-system fallback. For UI changes, exercise natal, synastry, composite and progressed views, including mixed known/unknown birth times, per-chart house/angle suppression, wheel-specific selection, transit-only navigation and progressed-only transit remapping. For personal transit-hit changes, test fixed targets, retrograde repeats, wrap rejection, DST-local day boundaries and exact-hit selection.

Follow the development commands in [README.md](README.md#development-and-contributions). Keep changes focused, update the relevant docs and changelog, and distinguish automated checks from devices/platforms you actually tested.

Contribute only material you have the right to submit. Contributions to this project are offered under **AGPL-3.0-or-later**, consistent with [LICENSE](LICENSE); preserve existing copyright notices and identify significant modifications. AI-assisted contributions are welcome when reviewed and tested by the contributor. Do not introduce private data, undisclosed proprietary dependencies or extra use restrictions.

## Source distribution

The footer offers **Source code** and **AGPLv3 or later** to everyone who can use the app. `/api/source` creates a ZIP from the source of the running release, rather than linking to a potentially different upstream version. Authentication is the same as for the app. `/api/license` serves the full license.

`source_bundle.py` deliberately packages an allowlist of project files. Runtime charts, passwords, ephemeris data, certificates, virtual environments, Git history and symlink targets are excluded. Keep secrets outside all source/documentation files: an allowlist cannot identify a password pasted into code.

When adding files, build steps or dependencies, update that allowlist and the `install.sh` release-copy list together. Include the complete preferred form for modification and the scripts needed to build, install and run your version. Do not replace the source offer with upstream code that omits your changes. If you distribute additional covered components, meet their corresponding-source obligations too; this helper is not a general-purpose compliance auditor.

Before a release, extract the source download into a clean folder, inspect its contents, run the checks, and verify the setup instructions. Keep the visible offer accessible to all remote users of a modified network version as required by AGPL section 13. Preserve required legal notices in modified interfaces. See the [GNU AGPL text](https://www.gnu.org/licenses/agpl-3.0.html) for the governing terms.
