# About this directory

`manifest.json` is the origin server's file catalog. Most entries here
are real files -- `index.html`, `style.css`, `script.js`,
`product.json`, and `api-data.json` are read from disk exactly as you
see them.

`favicon.ico`, `logo.png`, `banner.jpg`, and `video.mp4` are listed in
the manifest with a `simulated_size_bytes` field instead of a physical
file. Their actual bytes aren't relevant to anything this project
measures (routing, caching, latency), so rather than checking large
placeholder binaries into the repository, the origin server treats
them as metadata-only entries sized realistically enough for the
latency math to behave the way it would for real assets of that size.
See `origin_server.py` for how this is loaded.

## Assets and licensing

| File | In the repo? | Source / license |
|------|--------------|------------------|
| `favicon.ico` | No (size simulated) | Unknown -- no file exists |
| `logo.png` | No (size simulated) | Unknown -- no file exists |
| `banner.jpg` | No (size simulated) | Unknown -- no file exists |
| `video.mp4` | No (size simulated) | Unknown -- no file exists |

`index.html` no longer references any of them, since no real files
exist. They remain in `manifest.json` only so the simulation has
realistically sized files to cache. Before adding real media, record
where each file came from and confirm you have the right to use it. The
page uses the system font (Arial) and loads nothing from external
sites.

## Legal pages

`privacy.html` and `terms.html` are static pages linked from the footer of
`index.html`. They are deliberately not listed in `manifest.json`, so
they are not part of the simulated origin catalog and don't affect the
simulation.
