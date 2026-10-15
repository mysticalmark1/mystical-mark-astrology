# Changes

## 1.3.0

Combined release after 1.2.0; supersedes the earlier, unpublished transit-only 1.3.0 ZIP.

- Unknown birth time option for saved birth charts: date-only entry, local-noon normalization and per-chart suppression of houses, Ascendant, MC, Vertex, Fortune and Spirit.
- Unknown-time flags survive save/edit and JSON backup/restore; existing known-time records and other wheels retain their behavior. Progressions and composites derived from unknown-time sources retain appropriate omissions and warnings.

- Optional transit wheel for natal, composite, progressed and synastry charts (up to six base charts plus transits).
- Exact daily transit-to-natal/composite aspect hits, with fixed targets, wheel-specific selection and transit-local day boundaries.
- Time navigation, Now and date/location edits move only transits; fixed chart views no longer silently return to current sky.
- All existing aspect scopes, clearing, progressed-only view and synastry/composite conversion work with transits.
- Personal hits include selected Moon and true south node; fixed angles/lots may be targets. Moving angles/lots are excluded from exact-hit searches with a visible warning.
- SSH GitHub URLs for mysticalmark1, plus a reviewed rsync workflow, installation update steps and v1.3.0 tagging instructions.
- Existing chart conventions, database schema, authentication and HTTPS configuration unchanged.

## 1.2.0

- GitHub-ready README, installation, HTTPS/certificate, publishing and operations guides.
- Preserved AGPL-3.0-or-later terms; full license, SPDX notices, third-party notes and contribution/security policies.
- Visible license and running-source download links, with an allowlist excluding runtime data.
- Portable foreground launcher with native Windows/macOS data paths; explicit tzdata dependency. Native Windows/macOS installation remains untested.
- Generic public network defaults; Linux gateway setup now requires explicit IP/subnets. Existing installed gateway environment is preserved.
- Installer includes complete project source in each installed release.
- Source/privacy and portable-launcher regression checks. No calculation or database-schema changes.

## 1.1.0

- Selectable full aspect sidebar alongside the daily peak-moment view.
- Natal, composite and progressed charts default to their aspect lists.
- All / between-wheel / individual-wheel aspect scopes across sidebar, chart lines and table.
- Wheel-aware planet and aspect identities prevent duplicate planet highlights on other rings.
- Progressed-only view alongside natal/progressed biwheel.
- In-chart two-person composite conversion and return to synastry.
- Clear selection control, available in focus view.
- Selectable lower aspect-table entries and scrollable sidebar.
- Five state regression tests and an interaction smoke test.
- No calculation-method, database-schema or gateway changes.
