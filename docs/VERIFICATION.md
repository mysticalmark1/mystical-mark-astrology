# Verification record

## Release 1.2.0 update checks

- All 21 Python calculation/API/release tests passed on Linux with Python 3.12. New checks cover authenticated license/source routes, archive completeness and exclusion of runtime files/symlinks, portable path selection, private-address validation, password persistence and loopback-only launch arguments.
- All five JavaScript state tests and the DOM interaction smoke test passed again.
- Python compilation, JavaScript syntax and installer shell syntax passed. The portable Caddy example validated with Caddy 2.11.7.
- Native Windows/macOS startup, mobile certificate installation, service installation on a real desktop, and rendered browser QA were not executed. Path/launcher tests simulate platform selection; they do not replace native installation tests.
- TestClient reports an upstream deprecation warning for its HTTPX transport; all API tests pass.
- Calculation methods and the database schema remain unchanged.

## Release 1.1.0 update checks

- Five new JavaScript regression tests cover aspect aggregation/scopes, wheel-specific object identity, same-object cross-wheel aspects, progressed-only display, and cleared selections.
- A DOM interaction smoke test executes the actual HTML and JavaScript against deterministic chart API fixtures. It exercises the moments/aspects toggle, natal defaults, within/between/all filters, exact SVG wheel highlights, Clear selection, synastry→composite→synastry, progressed-only→biwheel, six-wheel scope selection, aspect-table clicks and event-time navigation.
- JavaScript syntax and installer shell syntax were checked. All 12 existing calculation/API tests passed again for this release.
- The calculation engine and database schema are unchanged; the API version string is updated. Browser-rendered visual QA on Zen/iPhone remains unperformed. The DOM test verifies interaction/state behavior, not pixel layout.

To run the DOM test, install `jsdom` in a development environment and run `node tests/ui-interactions.cjs` with that installation on `NODE_PATH`. The pure state tests require only Node: `node --test tests/chart-state.test.cjs`.

## Release 1.0.0 baseline verification

## Executed checks

- 12 automated calculation and API tests passed in the build environment (Python 3.12; FastAPI 0.143.0, Starlette 1.8.0, Uvicorn 0.54.0).
- Python source compiled successfully.
- JavaScript passed `node --check`; installer passed `bash -n`.
- Actual Astrodienst Swiss files downloaded through the application's download function. All four files completed: `sepl_18.se1`, `semo_18.se1`, `seas_18.se1`, `sefstars.txt`.
- A Swiss-mode chart successfully returned Sun, Moon, Mercury, Pluto, Chiron, Ceres and Regulus from those files, with Swiss return flags and no warnings.
- Generated Caddy configuration validated with official Caddy 2.11.7. Service-control calls were stubbed for that check; no user-machine services were changed.

## Numerical checks

| Check | Result |
|---|---|
| UTC → UT1 → UTC | Round trip better than 1 millisecond at the tested date |
| Spring DST missing time | Rejected |
| Autumn repeated time | First/second occurrences separated by one hour |
| Modern decan boundaries | Correct change at exact 10° and 20° boundaries |
| Angular wrap at ±180° | No false root at the discontinuity |
| Two roots around a relative-speed reversal | Both found in synthetic bracketing test |
| Missing Swiss data | Moshier fallback rejected |
| Saskatoon Placidus | 12 cusps; opposite cusps and object house assignment checked |
| Polar Placidus | Houses omitted with warning; no replacement house system |
| Mercury April 2024 station/shadows | Station speeds near zero; correct direction changes; shadow longitudes match opposite station endpoints |
| Aspect orb windows | Entry/exit residuals agree with configured orb in sampled daily events |
| Composite order | Swapping the two source charts preserves midpoint longitudes |
| Progression epoch | A 30-year target advances ephemeris time about 30 days |

Independent timing comparisons:

- April 8, 2024 New Moon: app **18:20:54 UTC**; US Naval Observatory **18:21 UTC** (minute-rounded table). [USNO API result](https://aa.usno.navy.mil/api/moon/phases/date?date=2024-04-01&nump=4), [service description](https://aa.usno.navy.mil/data/MoonPhases).
- April 1, 2024 Mercury retrograde station: app **22:14:33 UTC**; CHANI **3:14 PM Pacific daylight time**, equivalent to **22:14 UTC**. [Published cycle](https://www.chani.com/this-year/key-dates/2024-astrological-key-dates-mercury-retrogrades).

These are spot checks, not proof that every supported date/object/event is correct. A displayed second represents solver output; its physical accuracy also depends on ephemeris, Earth-rotation modelling and input data.

## API and storage checks

Missing authentication receives 401. Unknown Host headers, missing mutation-protection header and foreign origins receive 403. The main page includes restrictive content-security headers. Chart create/read/edit/delete, backup download, additive restore, single/synastry/composite/progressed modes, malformed import filenames, invalid download blocks and oversized event ranges were exercised.

## Not executed here

- Actual installation, restart, boot and rollback on Mark's Manjaro computer.
- Real LAN/WireGuard connections or firewall-rule interaction.
- Zen/iPhone visual layout, keyboard/touch interaction and print/PDF output in a browser.
- Exhaustive comparison of every asteroid, star, progressed-house convention or rare near-tangent event against independent software.

Browser automation was unavailable in the build environment; no screenshot-based visual QA is claimed. Keep existing trusted chart software available for comparison while introducing this new app into client or recorded work.

## First-run acceptance check

After installation, open today's chart, then verify a known birth chart against your existing software using identical location, time zone, tropical/geocentric settings, house method and ephemeris. Compare one Mercury station and a new/full moon. Save a sample chart, download its backup, and check print preview. Then open the phone HTTPS address over Wi-Fi and WireGuard. A browser certificate warning should be resolved by trusting the correct local CA, not by bypassing TLS verification.
