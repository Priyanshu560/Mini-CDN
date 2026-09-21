# Architecture

This goes one level deeper than the README: what each module actually
owns, the exact latency math, and the trade-offs behind a few
deliberate simplifications.

## Components

**`OriginServer`** is the single source of truth. It loads `data/manifest.json`
at startup, reads real content off disk for text files, and treats
files with a `simulated_size_bytes` entry as metadata-only (no bytes
held in memory -- see `data/README.md` for why). `update_file()` is the
only way a file's version changes, and it's what stands in for "someone
published a new version of this asset."

**`EdgeServer`** wraps an `LRUCache` and a `Network` profile. It never
talks to a client directly -- it's handed a file name, checks its
cache, and either serves what it has or falls back to the origin. It
has no idea a `Router` exists; routing decisions are made before an
edge is ever called.

**`Router`** does exactly one thing: given a client's location, compute
the haversine distance to every edge and return the closest one. With
only three edges this is a linear scan (`min()` over a dict), which is
fine at this scale -- see Future Improvements in the README for what
would replace it at a larger scale.

**`LRUCache`** is a generic, domain-agnostic cache -- it stores
arbitrary `(value, size_bytes)` pairs and knows nothing about
`FileObject`, versions, or the CDN at all. That separation is
deliberate: the eviction policy shouldn't need to change if the thing
being cached ever does.

**`Network`** models one server's link: a fixed base latency, a
bandwidth figure used to compute transfer time, jitter, and a small
failure probability. Both the origin and every edge own one.

**`Analytics`** only ever sees fully-resolved `Request` records. It
doesn't know how a request was routed or cached, just what happened to
it -- which keeps it reusable if the request pipeline ever changes.

**`RequestLogger`** wraps the standard `logging` module with a single
`FileHandler`, writing one structured line per request to
`logs/server.log`.

**`Simulator`** is the orchestration layer: it's the only place that
catches the domain-specific exceptions (`InvalidLocationError`,
`OriginFileNotFoundError`, `NetworkFailureError`) and turns them into a
uniform `Request` record with a `status` field, regardless of which
layer raised them.

## Latency Model

Every `Network` instance exposes:

```
transfer_time_ms(size_bytes) = size_bytes / (bandwidth_mbps * 125)
round_trip_ms(size_bytes)    = base_latency_ms + transfer_time_ms(size_bytes)
```

(1 Mbps is 125 bytes/ms, so that constant is just a unit conversion.)

**On a cache hit**, the edge serves the client directly:

```
latency = edge.round_trip_ms(size) + edge.jitter()
```

**On a miss or a stale hit**, the edge has to pull from the origin
first, then deliver to the client -- two hops, each with its own base
latency and transfer time:

```
latency = origin.round_trip_ms(size) + edge.round_trip_ms(size) + edge.jitter()
```

This is why a cache hit on `video.mp4` from Delhi resolves in roughly
110-140 ms, while a miss for the same file resolves in the 350-370 ms
range -- the origin's 180 ms base latency plus its own transfer time
gets paid twice: once implicitly by existing at all, and once by
adding to the edge's own hop.

## Cache Invalidation

MiniCDN uses **lazy (pull-based) invalidation**: an edge only discovers
its copy is stale when a client happens to request that file again and
the version numbers don't match. There's no push/purge API telling
edges to drop something proactively.

This is a real trade-off, not just a simplification for its own sake:
it keeps the whole simulation single-threaded and easy to reason about,
and it mirrors how a lot of real caches behave without a dedicated
invalidation channel. The cost is that a stale file can keep being
served by an edge indefinitely if nobody happens to ask for it again
after the origin changes -- which is a fair question to expect in an
interview, and "add TTL-based expiry alongside version checks" in the
README's Future Improvements is the direct answer to it.

One implementation detail worth calling out: `EdgeServer` caches a
**copy** of the file object (`dataclasses.replace(origin_file)`), not a
live reference to the origin's own object. Caching the reference
directly was an actual bug during development -- since `FileObject` is
mutable, every edge that had ever cached it would see the origin's
version bump too, because they'd all be pointing at the same object in
memory. The version check would then always pass, and staleness would
never be detected. The fix, and the regression test for it, are in
`edge_server.py` and `tests/test_edge_server.py`.

## Known Simplifications

- Failed requests (`INVALID_LOCATION`, `FILE_NOT_FOUND`, `NETWORK_FAILURE`) report 0 ms latency. In reality, even a failed lookup takes some round-trip time.
- Routing is a linear scan over edges. Fine for three; would need a spatial index at real CDN scale.
- Large binary files (`video.mp4`, `banner.jpg`, `logo.png`, `favicon.ico`) are represented by simulated size only, not actual bytes -- see `data/README.md`.
- Analytics live only for the lifetime of the process; nothing is persisted between runs.
