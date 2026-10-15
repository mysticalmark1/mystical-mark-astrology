# Mystical Mark Astrology

**A private, self-hosted astrology workspace for forecasts, chart exploration and client readings.**

[AGPLv3 or later](LICENSE) · [Calculations & references](docs/CALCULATIONS.md) · [HTTPS & certificate setup](docs/HTTPS.md) · [Contributing](CONTRIBUTING.md) · [Changelog](docs/CHANGELOG.md)

Mystical Mark Astrology runs a Python server on your own computer and opens in your browser. Its purple-and-gold interface is designed for readings, screen sharing and recorded forecasts. Your chart collection stays on the host computer. The app does not require a subscription or a cloud account.

Created for [Mystical Mark](https://mysticalmark.ca), and shared so others can inspect the calculations, run their own instance, improve it and fork it. This project was developed with AI assistance; source, conventions, tests and known limits are included for review. It is not independently certified astrology software.

**Current release: 1.3.0.** This combined release upgrades directly from 1.2.0 and includes transit overlays plus unknown birth times.

## Features

| Area | What you can do |
|---|---|
| Chart room | Tropical, apparent geocentric charts; modern triplicity decans; Placidus or no houses; date/time navigation and a recording-friendly focus view |
| Aspect exploration | Toggle daily peak moments versus all current chart aspects; select planets or aspects; clear selection without moving time |
| Multiple wheels | Two to six synastry wheels; filter all aspects, between-wheel aspects or one wheel's internal aspects; wheel-specific highlighting |
| Transit overlays | Add a transit wheel to natal, composite, synastry or progressed views; advance only transits while keeping base charts fixed; daily exact transit-to-natal/composite hits |
| Relationships | Two-person short-arc midpoint composite; convert a synastry biwheel into a composite directly from the chart and back |
| Progressions | Direct day-for-year secondary progressions, displayed alone or beside the natal chart; explicitly labelled house conventions |
| Forecast planning | Daily or up-to-31-day event timeline with exact aspects, ingresses, stations, shadow boundaries and major lunar phases; Markdown export with space for your own notes |
| Retrogrades | Annual cycles with pre/post-shadow endpoints, sign changes and decans traversed; object and date filters |
| Objects & aspects | Planets, supported nodes/lots/angles, main asteroids, additional numbered asteroids and catalogued fixed stars; adjustable orbs and custom longitude angles |
| Ephemerides | Built-in Moshier, or explicit downloads of Swiss data from Astrodienst's official repository; visible missing-data warnings rather than silent fallback |
| Unknown birth times | Date-only birth records calculated at local noon, with houses and time-dependent points suppressed for that chart only |
| Records & exports | Saved natal inputs and private notes; additive JSON backup import; SVG wheel export; light/dark browser print-to-PDF |
| Private access | Password-protected loopback server; optional Caddy HTTPS gateway restricted to your LAN/VPN |

“All aspects” means enabled aspects **within the configured orbs**, not every possible pair regardless of separation. Birth charts show natal aspects. With a transit wheel, natal/composite views also offer exact personal hits for the selected transit day. The separate Transit timeline remains a mundane sky timeline. No interpretations are automatically generated.

## Platform support

| Platform | Status |
|---|---|
| Linux with systemd | Primary installation path: release installer, user service, optional Caddy gateway and boot startup. Manjaro is the original target. |
| Other Linux systems | Manual foreground setup using `run.py`; use your OS's service manager for unattended operation. |
| Windows / macOS | Portable foreground setup provided. The code has been adapted for native data paths and Windows time-zone data, but native installation and browser operation have **not** been tested on these systems. |
| iPhone / iPad / Android | Browser clients of an existing host over Wi-Fi or VPN. They do not run the Python server. |

Use **64-bit CPython 3.12** for the most reproducible setup. Other Python versions and CPU architectures are not covered by the verification record. `pyswisseph` includes native code: if no compatible wheel exists, a C/C++ compiler is needed. This is a Python web app, not a packaged Windows/macOS installer or a public multi-user hosting service.

## Get the source

Download and extract a release source ZIP, or clone the public repository:

```bash
git clone git@github.com:mysticalmark1/mystical-mark-astrology.git
cd mystical-mark-astrology
```

Public read-only HTTPS cloning also works without a GitHub account: `git clone https://github.com/mysticalmark1/mystical-mark-astrology.git`.

## Linux installation with automatic startup

Install prerequisites for your distribution. Caddy is optional unless you want another device to connect.

**Manjaro / Arch:**

```bash
sudo pacman -S --needed python python-pip base-devel caddy git
```

**Debian / Ubuntu:**

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip python3-dev build-essential git
```

For Caddy, follow its [official installation instructions](https://caddyserver.com/docs/install). Distribution packages vary; confirm your Python version with `python3 --version`.

From the source folder, run this **as your normal user, without sudo**:

```bash
bash install.sh
```

The installer creates an isolated virtual environment, checks a sample chart, installs a separate release and starts a systemd user service. It prints a generated password. The fixed local username is **`mark`** (a local app login, unrelated to your GitHub or OS account).

Open **http://127.0.0.1:8876** and sign in. Internet access is needed to install dependencies and when explicitly downloading ephemeris data; ordinary calculations and saved-chart access work locally.

To start before desktop login:

```bash
sudo loginctl enable-linger "$USER"
```

Your home directory must be available at boot. This installer requires Linux/systemd and a home path without spaces or `%` characters. It does not alter other applications' Caddy configurations, firewall rules or databases.

## Portable setup: Windows, macOS or manual Linux

These commands keep the server in the foreground. Closing the terminal or pressing Ctrl+C stops it. Run from the project directory. Do not run a portable instance alongside an installed instance on the same port.

### Windows — PowerShell

Install 64-bit Python 3.12 from [python.org](https://www.python.org/downloads/). If `pyswisseph` must compile, install Microsoft's [Build Tools for Visual Studio](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio) with the **Desktop development with C++** workload and Windows SDK, then retry in a new terminal.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py --show-password
.\.venv\Scripts\python.exe run.py
```

No PowerShell activation-policy change is required. Open **http://127.0.0.1:8876**, username `mark`, and use the displayed password.

### macOS

Install Python 3.12 from [python.org](https://www.python.org/downloads/macos/). If a dependency needs compiling, install Apple's command-line developer tools:

```bash
xcode-select --install
```

Then:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run.py --show-password
.venv/bin/python run.py
```

### Manual Linux

Install Python/venv/compiler prerequisites, then:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run.py --show-password
.venv/bin/python run.py
```

The portable launcher uses the same loopback-only server and password protection. `tzdata` supplies IANA time-zone data when the OS lacks it, notably on Windows. Automatic Windows Services, Task Scheduler and macOS launchd setup are not included in this release. See [Caddy's service guide](https://caddyserver.com/docs/running) if you choose to manage services yourself; run each process under the same account/data directory used for setup.

## HTTPS, phones and VPN

Local desktop use at `127.0.0.1` needs no certificate setup. Use HTTPS for another device. The default backend port is **8876**; the optional private HTTPS gateway uses **9444**. Neither should be forwarded from your router to the public internet.

For the Linux installer, configure your actual private IPv4 address and source subnets. The values below are **examples**, not automatic network discovery:

```bash
"$HOME/.local/lib/mystical-mark-astrology/current/.venv/bin/python" \
  "$HOME/.local/lib/mystical-mark-astrology/current/manage.py" lan \
  --ip 192.168.1.50 --cidrs 192.168.1.0/24
```

Add your actual VPN subnet to `--cidrs` separated by a comma if needed. Open `https://192.168.1.50:9444` using the address you configured. Keep a stable LAN address (for example a router DHCP reservation).

**[Follow the HTTPS guide](docs/HTTPS.md)** for portable Caddy configuration, firewall/VPN requirements, certificate locations, and trust instructions for Windows, macOS, Linux, iOS/iPadOS, Android and Firefox/Zen. Trust the host's root certificate on each client; never distribute its private keys or bypass certificate verification.

## First chart and weekly workflow

1. In **Settings**, verify your default location, latitude/longitude and IANA time zone (e.g. `America/Regina`). The initial sample location is Saskatoon; change it for your own use. Place labels do not geocode or infer time zones. West/south coordinates are negative.
2. Choose Moshier, or download Swiss data and then select Swiss and save. Missing objects are reported. No unsupported position is invented.
3. Select objects, aspect definitions and orbs. Only modern triplicity decans are implemented. Houses are either Placidus or off.
4. In **Chart room**, select the time and navigate by minute, hour, day, week or month. The default step is one local calendar day.
5. Choose **Peaking on this day · moments** to jump to exact events, or **All chart aspects** to explore the current chart without changing time. Clear selection removes highlighting. Focus view reduces recording clutter.
6. Use **Transit timeline** to plan 1–31 days and export Markdown. Ordinary Moon aspects are hidden from that timeline by default; major lunar phases remain visible.
7. Use **Retrogrades & shadows** for annual cycles, optional objects and narrower date filters. Cycles can span year boundaries.

## Client and relationship readings

**Saved charts → New chart** stores a name, local time, IANA zone, coordinates and optional private notes. Choose first/second occurrence for a duplicated autumn DST time. A nonexistent spring-forward time is rejected. Verify birth records and historical time-zone choices yourself.

Select one record for a natal chart or secondary progression, two for a composite, and two to six for synastry. Selection order determines ring order. In a multiwheel view, filter aspects by all, between wheels or a particular wheel. Planet selections identify their specific ring.

**Progressions:** enter the real-life target date/time in the natal record's zone. Use **Natal + progressed / Progressed only** above the chart. The default uses natal reference houses; optional quotidian houses are explicitly labelled. The full convention is in [CALCULATIONS.md](docs/CALCULATIONS.md).

**Composites:** a two-wheel synastry view offers **Make composite** and **Back to synastry**. These use the same saved inputs and do not modify them. Only the short-arc midpoint method is implemented, not Davison. Degenerate midpoint/house cases warn rather than silently inventing a result.

Use **Export SVG** for the wheel image. **Print / PDF · light** produces an ink-friendly browser print layout; choose Save to PDF in your browser. Dark print mode is also available. Printed output includes chart/source details and the selected-scope aspect table.

## Unknown birth time

In **Saved charts → New chart** or **Edit**, select **Unknown birth time · use local noon**. The form asks for the birth date instead of a time. Keep the correct IANA time zone, location and coordinates: this chart uses **12:00 noon on that date in that time zone**, not noon UTC. To enter a known time later, edit the record, clear the checkbox, and enter the actual birth time.

For that record, the app always omits **houses, Ascendant, MC, Vertex, Part of Fortune and Part of Spirit**, even if Placidus is checked in the chart room or those points are enabled in Settings. It does not change global settings. Other known-time charts in synastry, and a known-time transit wheel, retain their own houses and selected points. The shared wheel's house grid follows its first/base chart; each chart's placements still report its own available houses.

Unknown-time records are labelled in saved charts, chart legends and warnings. Noon is an assumption: positions—especially the Moon—and resulting aspects, progressions and personal transit-hit timings are approximate relative to the actual unknown birth instant. An exact transit hit is exact to the **assumed noon chart**, not a recovered birth time.

A progression from an unknown-time birth remains without houses/time-dependent points under either progression-house setting. A composite with either source time unknown likewise omits houses and those points and carries the noon-assumption warning. Other known-time source charts are unchanged.

The flag is stored with the chart and included in JSON backup/restore. Existing records without the flag retain their known-time behavior. No database-schema migration is needed. Use version 1.3.0 or newer for unknown-time records: older versions do not interpret this flag and may display misleading noon-based houses.

## Transit wheels and personal exact hits

Open a saved birth chart, progression, synastry or composite, then click **Add transit wheel** in the chart toolbar. The transit wheel starts at the current time using the default location/time zone from Settings. **Transit date & location** lets you choose another time, zone, DST occurrence and place. Removing and re-adding it reuses your last transit inputs during this browser session.

- **Previous / next / Now / Transit date & location** change only the transit wheel. Natal inputs, composite positions, synastry participants and the progression target remain fixed. Advancing a day/week/month uses local calendar time; a repeated DST time defaults to its first occurrence and a nonexistent local time is rejected. Use the dialog to choose the second occurrence explicitly.
- **Birth chart + transits** and **composite + transits** offer **Peaking on this day · moments**: exact transiting-object aspects to the fixed chart during the selected transit-local calendar day. This includes hits earlier and later than the currently displayed time. Click one to move only the transit wheel to that hit and highlight its exact pair of objects.
- **All chart aspects** remains available, with all / between-wheel / individual-wheel filters. These show enabled aspects within your configured orbs at the displayed time. Synastry and progressed overlays use these aspect lists; personal exact-hit timelines for those modes are not included.
- **Progressed only** hides the natal reference wheel and retains the transit wheel. The existing natal/progressed option becomes three wheels when transits are enabled. Synastry supports six base charts plus a transit wheel.
- Converting two-person synastry to a composite and back preserves the transit date/location. **Remove transit wheel** returns to the underlying chart; **Current sky** explicitly leaves the saved-chart view.

The selected Moon participates in personal exact hits even if ordinary Moon aspects are disabled for the mundane timeline. Fixed natal/composite angles and lots can be targets; moving angles/lots are excluded from the exact-hit solver and reported in its warnings, but remain selectable in the aspect lists. Personal hit searches do not calculate orb-entry/exit windows. No exact hit on a day does not mean no in-orb aspects: switch to All chart aspects.

Time controls are disabled on a fixed saved-chart view without a transit wheel, preventing accidental replacement by the current sky. Transit overlays are temporary viewing state, not extra saved birth records. Existing saved charts and notes are unchanged. See [calculation conventions](docs/CALCULATIONS.md#personal-transit-hits).

## Additional ephemeris objects

The download action gets Swiss planetary, lunar, main-asteroid and fixed-star data for the selected block from [Astrodienst's official repository](https://github.com/aloistr/swisseph). It does not download the entire numbered-asteroid collection or raw multi-gigabyte JPL kernels.

For additional asteroids, obtain their official `.se1` files via [Astrodienst's data instructions](https://www.astro.com/ftp/swisseph/ephe/), import them in Settings, then add `10000 + catalog number` to Extra objects. Example: asteroid 433 Eros is object `10433`. The importer chooses the correct `astN` folder. Date coverage varies by file.

For stars, add a lookup such as `star:Regulus`; the name must be available in `sefstars.txt`. A star aspect here compares ecliptic longitude, not angular separation on the celestial sphere.

## Data, backups and updates

| Installation | Default private data directory |
|---|---|
| Linux (installer or launcher) | `~/.local/share/mystical-mark-astrology/` |
| Windows portable launcher | `%LOCALAPPDATA%\MysticalMarkAstrology\` |
| macOS portable launcher | `~/Library/Application Support/MysticalMarkAstrology/` |

`MM_ASTRO_DATA` can override the portable launcher's path. Always use the same path/account when restarting. The database, password and ephemerides live outside the source checkout. Permissions restrict files on POSIX systems; on Windows, keep the data in your private user profile and use Windows permissions/disk encryption as appropriate. The app does not encrypt its database itself.

**Backups:** Saved charts → Download complete backup exports chart inputs, notes and settings. It excludes passwords and ephemeris files. Import adds new records and restores settings; importing twice creates duplicates. A local SQLite snapshot is made before import.

**Linux updates:** download a new release or pull changes into a source checkout, then run `bash install.sh` as the same user. It snapshots the database, builds/checks a new environment, switches the release and restarts the backend. Existing chart data and gateway configuration remain. Refresh your browser afterward. Upgrading from 1.2.0 to 1.3.0 needs no database migration and no new Caddy setup. Existing configured private hosts are preserved in the installer-managed environment file.

**Portable updates:** download a backup, stop the app, extract the new release into a separate source folder, create its virtual environment and install its dependencies, then restart `run.py` with the same data path and `--lan-host` if used. This method does not create the installer's automatic pre-update snapshot; the backup step matters. Keep your old source folder until the new version works.

See [Operations](docs/OPERATIONS.md) for service logs, password access, rollback and removing the app without deleting records.

## Calculation scope and limits

- Tropical apparent geocentric charts, Gregorian dates **1800–2399**; mundane event/retrograde windows **1803–2395** to allow search padding; personal exact-hit days **1800–2398**.
- Placidus or no houses. Polar Placidus failures omit houses with a warning. House membership uses ecliptic longitude between cusps.
- Supported calculated points include mean/true nodes, true south node, mean/osculating Lilith, Ascendant, MC, Vertex, and day/night Fortune/Spirit. Arbitrary point formulas are not included.
- Aspects are ecliptic-longitude aspects with configurable angles/orbs. Declination parallels/contraparallels are not included.
- The mundane timeline excludes rapid house-angle/lot and derived south-node exact-event searches. Personal hits include moving true south node, but exclude moving angles/lots. Their placements and chart aspects are available. Orb-boundary searches have finite limits and label missing results.
- No offline world atlas, BCE/historical-calendar conversion, Naibod progressed angles or multi-day personal-hit export.
- Very crowded multiwheel charts and exotic/high-speed objects need additional validation. Solver timestamps do not imply second-level observational accuracy or validate astrological interpretations.

Read [calculation conventions and primary references](docs/CALCULATIONS.md), [verification results](docs/VERIFICATION.md) and [security scope](SECURITY.md) before relying on this new application. Linux calculation/API tests and DOM interaction checks have been run; visual browser QA and native Windows/macOS deployment remain unverified.

## Development and contributions

The backend uses FastAPI, SQLite and pyswisseph. The frontend is plain HTML/CSS/JavaScript; there is no frontend build step.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
node --test tests/chart-state.test.cjs
node --check app/static/app.js
```

On Windows, use `.\.venv\Scripts\python.exe` in place of `.venv/bin/python`. Node is needed only for frontend tests. See [verification instructions](docs/VERIFICATION.md) for the DOM smoke test and [CONTRIBUTING.md](CONTRIBUTING.md) for calculation-change expectations and contributor licensing.

## License and transparency

This project is licensed under the **GNU Affero General Public License, version 3 or any later version**: `AGPL-3.0-or-later`. The complete, unmodified license is in [LICENSE](LICENSE); project attribution is in [NOTICE](NOTICE). This preserves the terms supplied with earlier releases.

You may use, study, modify, fork and redistribute it, including commercially, subject to the license. Preserve required notices and follow the applicable corresponding-source obligations. Section 13 requires modified network-interactive versions to prominently offer their corresponding source to their remote users.

The app's **Source code** link offers its local project source to signed-in users and its **License** link displays the license. Fork maintainers must keep the offered source complete and matched to their running version, including any extra build/install material or dependencies they distribute; the helper cannot automatically know about files they add outside its allowlist. See [source distribution notes](CONTRIBUTING.md#source-distribution).

Swiss Ephemeris is developed by **Astrodienst AG**; pyswisseph is maintained upstream by its own contributors. This project is not an Astrodienst product or endorsement. Dependencies keep their own licenses: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). No private client data or ephemeris binaries are bundled in this source release. Software is provided **without warranty** as set out in the license.

Official references: [GNU AGPLv3](https://www.gnu.org/licenses/agpl-3.0.html) · [GNU license application guidance](https://www.gnu.org/licenses/gpl-howto.html) · [Swiss Ephemeris](https://www.astro.com/swisseph/).
