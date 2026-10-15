# Calculation conventions and sources

These notes specify this application's behavior. They are not a claim that all astrology programs use the same conventions.

## Coordinates and clocks

The engine uses `pyswisseph` 2.10.3.2 and its bundled Swiss Ephemeris library. Position flags request apparent tropical geocentric ecliptic coordinates of date and longitude speed. Sidereal, heliocentric and topocentric modes are not offered. Local civil time is resolved using Python's IANA `zoneinfo`; UTC is converted through Swiss Ephemeris to UT1 before position/house calculations. East longitude and north latitude are positive. Dates use the proleptic Gregorian calendar within the advertised range.

The API checks returned ephemeris flags. In Swiss mode, Moshier fallback is rejected and the omitted object is reported. Some objects require external files even when the planetary engine selector is Moshier. The app records the actual engine with each position.

Primary references:

- [Swiss Ephemeris programmer interface](https://www.astro.com/swisseph/swephprg.htm)
- [Official Python extension and API](https://github.com/astrorigin/pyswisseph)
- [Python zoneinfo documentation](https://docs.python.org/3/library/zoneinfo.html)

## Placidus and calculated points

`houses_ex(..., b'P')` produces tropical Placidus cusps. A polar calculation failure removes the houses and dependent points with an explicit warning. A substitute house system is not displayed. The wheel assigns houses by the object's **ecliptic longitude between cusps**, rather than a latitude-aware mundane house position. The boundary cusp belongs to the following house.

The true south node is exactly opposite the true north node. Ascendant, MC and Vertex come from the house calculation. Fortune is Ascendant + Moon − Sun by day and Ascendant + Sun − Moon by night. Spirit uses the inverse luminary arc. Day/night is determined by the true geometric altitude of the Sun's center, with day at altitude ≥ 0°, rather than atmospheric refraction. These angle-dependent points are omitted if the Placidus calculation fails.

## Modern decans

Each sign contains three half-open 10° intervals: [0,10), [10,20), [20,30). The associated signs advance through the same element: the sign itself, then +4 signs, then +8 signs. Modern rulers are used: Scorpio/Pluto, Aquarius/Uranus and Pisces/Neptune. Example: Aries decans are Mars, Sun, Jupiter. No Chaldean decans are implemented.

Reference: [Astrodienst — Decan, including the modern triplicity system](https://www.astro.com/astrowiki/en/Decan).

## Aspects and event solving

For object longitudes λA and λB, the signed shortest difference is wrapped to [−180°,180°). Aspect separation is its absolute value. A longitude aspect is within orb when `abs(separation − aspect_angle) ≤ configured_orb`. All objects use that aspect's configured orb; there is no hidden luminary bonus. The intra-chart applying indicator uses the sign of the longitude-separation derivative. Cross-chart and composite applying/separating labels are intentionally left blank because they are not an ordinary two-body evolving sky.

The app's custom event algorithm brackets exact longitude-difference roots on a three-hour grid, splits an interval at a detected relative-speed reversal, rejects ±180° wrap discontinuities, and bisects the remaining bracket to 0.1 seconds of time. Ingresses use six-hour intervals, splitting at stations when necessary. Longitude-speed sign changes identify direct/retrograde stations. Numerical precision does not equal observational accuracy, and a sampled algorithm is not a mathematical completeness proof for every exotic orbit.

An event's orb interval is the contiguous in-orb passage containing that exact hit, searched to the nearest entry/exit on either side. A later retrograde return may share that interval if the aspect never leaves orb. Search limits are ±800 days. Missing boundaries are returned as missing, not as the beginning or end of a selected week. Four major lunar phases always use Sun–Moon elongations 0°, 90°, 180° and 270° even if ordinary Moon aspects are disabled.

The preset catalog contains major aspects and semisextile, semisquare, sesquiquadrate, quincunx, quintile/biquintile, septile-family, novile-family, decile/tridecile, undecile-family and selected finer divisions. Custom numerical angles allow additional longitude harmonics. Names/glyphs for minor aspects are not universally standardized; unusual aspects are labelled rather than given fabricated traditional symbols. Declination aspects are outside this release's scope.

## Retrogrades and shadow periods

A cycle pairs a positive→negative longitude-speed zero with the next negative→positive zero. The pre-shadow starts at the preceding direct crossing of the later direct-station longitude. The post-shadow ends at the following direct crossing of the earlier retrograde-station longitude. Stations are searched in a padded annual interval; cycles intersecting the requested year, including those crossing year boundaries, can be returned. The browser applies the chosen local date filter.

Each phase lists its endpoints, sign ingresses and decans traversed. This longitude-loop definition is applied to supported retrograding objects without adding interpretive claims. Always-retrograde mean nodes are excluded as having no ordinary paired station cycle. True nodes and osculating apogees can produce unusual loops; those results warrant comparison with another implementation before use.

References:

- [Astrodienst / OPA — 2023 Venus cycle and shadow-degree crossings](https://www.astro.com/astrology/opa_article230704_e.htm)
- [CHANI's independently published 2024 Mercury timing table](https://www.chani.com/this-year/key-dates/2024-astrological-key-dates-mercury-retrogrades)

## Secondary progressions

The implementation is direct secondary progression with a fixed mean-tropical-year key:

```text
progressed_UT1_JD = birth_UT1_JD + (target_UT1_JD − birth_UT1_JD) / 365.242190402
```

The displayed progressed positions are actual ephemeris positions at that symbolic instant. The exact time key is a documented convention, so programs using another year length may differ slightly. The target is interpreted in the natal chart's recorded zone. It must be entered as the real-life target date, not manually converted to days after birth.

Default house display: **natal Placidus reference houses** on the natal/progressed biwheel. Progressed angle-dependent points are omitted in that mode rather than mislabelled. Optional **quotidian** houses are Placidus at the actual progressed instant and natal location. This is explicitly not a Naibod or solar-arc angle calculation.

References:

- [Astrodienst chart-type overview](https://www.astro.com/faq/fq_fh_owtype_e.htm)
- [Kepler College — Introduction to Secondary Progressions](https://library.keplercollege.org/into-secondary-prog/)

## Synastry and composite

Synastry retains each record's actual longitudes and shows two to six rings. Cross-aspects compare all distinct chart pairs. The first ring provides reference houses for the wheel; individual placements retain their own natal house numbers in their placement records.

Composite longitudes use `A + wrap(B−A)/2`, modulo 360. This is a short-arc ecliptic midpoint, symmetric under exchanging charts. An exact antipodal pair is ambiguous and is rejected. Midpoint cusps are derived from corresponding natal Placidus cusps, not calculated from an invented date or place. If those midpoint cusps fail to form a single ordered circuit, the app removes composite houses and warns instead of silently flipping cusps. Composite speed, retrograde status and applying/separating motion are not treated as physical sky quantities. Selected natal calculated points are midpointed like other selected longitudes; Fortune/Spirit are not recomputed from composite luminaries.

No Davison chart exists in this application.

Reference: [Astrodienst composite explanation](https://www.astro.com/faq/fq_fh_compo_e.htm).

## Swiss files and provenance

The download action uses Astrodienst's official `aloistr/swisseph` repository over HTTPS. Each selected block includes `sepl`, `semo`, `seas` and the fixed-star catalog. Downloads are size bounded, validate a Swiss file header, replace files atomically, and record SHA-256 hashes and download time in the local manifest. Hashes identify downloaded bytes; they are not an independent upstream signature. The files can be redownloaded deliberately as Astrodienst updates them.

Additional asteroid files are imported from official `.se1` files. The application validates filename/header, derives the `astN` directory from the asteroid number, and blocks path traversal. File date coverage still matters; a catalog number does not guarantee an ephemeris exists for every date.

References:

- [Astrodienst official download instructions](https://www.astro.com/swisseph/swedownload_e.htm)
- [Astrodienst's official source and data repository](https://github.com/aloistr/swisseph)
- [Numbered-asteroid download locations](https://www.astro.com/ftp/swisseph/ephe/)

## Private gateway references

The local gateway uses Caddy's explicit interface binding, socket remote-IP matching, internal TLS and separate global options. It does not trust incoming `X-Forwarded-For` values for its allowlist. The Python backend is loopback-only and does not process proxy headers as client identity.

- [Caddy bind directive](https://caddyserver.com/docs/caddyfile/directives/bind)
- [Caddy remote_ip matcher](https://caddyserver.com/docs/caddyfile/matchers#remote-ip)
- [Caddy global options](https://caddyserver.com/docs/caddyfile/options)
