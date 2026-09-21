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
