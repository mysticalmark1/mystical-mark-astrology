# Third-party components

This source archive contains the project's own source and documentation, not a bundled Python interpreter, virtual environment, Caddy executable or Swiss ephemeris data. Installation fetches the dependencies listed in `requirements.txt`; they retain their own licenses. The project's AGPL does not replace upstream notices.

## Swiss Ephemeris and pyswisseph

- **Swiss Ephemeris**, developed by Astrodienst AG: [official project and licensing](https://www.astro.com/swisseph/), [source and data repository](https://github.com/aloistr/swisseph). Its free-software licensing option is the GNU AGPL; a separate professional license is offered by Astrodienst. This project uses the free-software option.
- **pyswisseph**, the Python binding used by this app: [upstream source and license](https://github.com/astrorigin/pyswisseph), [package distribution](https://pypi.org/project/pyswisseph/). The installed package declares GNU AGPLv3. Preserve the exact notices accompanying the version you distribute.
- Swiss files are downloaded only on explicit user action from Astrodienst's repository. Numbered-asteroid imports and fixed-star catalogue contents remain upstream material. This ZIP does not redistribute those data files. The app's download manifest records downloaded file information.

## Runtime and development dependencies

The principal web/runtime components include FastAPI (MIT), Starlette (BSD-3-Clause), Uvicorn (BSD-3-Clause), Pydantic and pydantic-core (MIT), AnyIO (MIT), and tzdata (Apache-2.0, with upstream time-zone data notices). Other pinned packages and transitive dependencies have their own licenses; consult the installed distribution's metadata and license files. Python itself is separately licensed by the Python Software Foundation.

Development checks use pytest, HTTPX and optionally jsdom. Caddy is a separately installed HTTPS server under Apache-2.0; see [Caddy's license](https://github.com/caddyserver/caddy/blob/master/LICENSE). No third-party frontend bundle, CDN script or webfont is shipped by this app.

## Redistributing more than this source tree

If you distribute an executable, container, virtual environment, dependency bundle or ephemeris data, include the applicable upstream notices and licenses and satisfy each component's source/distribution requirements. This inventory is not a substitute for the exact license files in those distributions. Keep the offered corresponding source matched to what you ship and run. See [CONTRIBUTING.md](CONTRIBUTING.md#source-distribution).

Names and links identify dependencies; they do not imply endorsement by Astrodienst or any other upstream project.
