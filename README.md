# MiniCDN

A from-scratch simulation of how a content delivery network routes,
caches, and serves files across geographically distributed edge
servers. The routing decision, the LRU cache, the latency model, and
the invalidation logic are all implemented directly rather than
pulled from a library, since the point is to demonstrate the
mechanics, not just call something that already does this.

## Overview

MiniCDN models a single origin server backed by three edge servers
(Delhi, Mumbai, Bangalore). A client submits a name, a location, and
a file name; the router picks whichever edge is geographically
closest using the haversine formula; that edge checks its own LRU
cache and either serves the file directly or pulls a fresh copy from
the origin. Every request is timed, logged, and folded into running
analytics, and the whole thing can be driven either from a CLI or a
small Flask API.

The project is split into narrow, single-purpose modules so caching,
routing, latency, and analytics can each be read, tested, and
explained on their own.

## Architecture

```
                         +----------------+
                         |     Client     |
                         |  name/location |
                         +--------+-------+
                                  |
                                  v
                          +--------------+
                          |    Router    |  --- picks nearest edge
                          +------+-------+      (haversine distance)
                                 |
              +------------------+------------------+
              |                  |                   |
              v                  v                   v
      +---------------+  +---------------+  +----------------+
      |  Edge: Delhi  |  |  Edge: Mumbai |  | Edge: Bangalore|
      |   LRU Cache   |  |   LRU Cache   |  |   LRU Cache    |
      +-------+-------+  +-------+-------+  +-------+--------+
              |                  |                   |
              +------------------+-------------------+
                                 |
                       cache miss / stale version
                                 |
                                 v
                        +----------------+
                        |  Origin Server |
                        |  file catalog  |
                        +----------------+
```

Request flow, in order:

1. A client (name + location) asks for a file.
2. `Router` resolves the client's city to coordinates and picks the edge server with the smallest haversine distance to it.
3. That `EdgeServer` checks its own `LRUCache` for the file: cached and version matches the origin is a **HIT**; cached but the origin has moved on to a newer version is **STALE**; not cached at all is a **MISS**.
4. On a miss or a stale hit, the edge fetches a fresh copy from the origin, caches it (evicting the least-recently-used entry if it needs the room), and serves it.
5. Latency is computed from each hop's base latency, transfer time (file size ÷ bandwidth), and random jitter.
6. The result is written to `logs/server.log` and folded into the running `Analytics`.

`docs/architecture.md` goes deeper into the exact latency formulas and a few deliberate simplifications.

## Features

- Distance-based routing across nine Indian cities using the haversine formula, with three of them also acting as edge locations
- A byte-budgeted LRU cache per edge server, built from scratch on `OrderedDict`
- Version-based cache invalidation: edges detect a stale copy lazily, the next time it's requested, and resync automatically
- A latency model combining base network latency, size-based transfer time, and random jitter, plus a small simulated failure rate per server
- An event-driven batch simulator that schedules requests on a `heapq` priority queue and processes them in simulated arrival order
- Full request analytics: hit/miss ratio, average/median/fastest/slowest latency, per-server load, and the most requested file
- Structured, greppable logging to `logs/server.log`
- Matplotlib charts for cache hits vs. misses, latency distribution, requests per server, and per-edge cache utilization
- An optional Flask JSON API that drives the same simulation as the CLI
- 35 unit and integration tests across 7 test modules

## Screenshots

_Run a batch simulation (`python main.py 500`), then drop a screenshot of the CLI output and a couple of the generated charts from `docs/charts/` here._

## Installation

```
git clone <your-fork-url>
cd mini-cdn
python3 -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Requires Python 3.9+. No database, no Docker, nothing else to configure.

## Usage

### CLI

```
python main.py            # interactive menu
python main.py 500        # run 500 simulated requests, print analytics, generate charts, and exit
```

Example interactive session:

```
Choose an option: 1
Client name: Ravi
Client location ['Delhi', 'Mumbai', 'Bangalore', 'Punjab', 'Jaipur', 'Lucknow', 'Kolkata', 'Hyderabad', 'Ahmedabad']: Punjab
Requested file: video.mp4

Server selected : Delhi
Cache status    : MISS
Latency         : 361.16 ms
Status          : SUCCESS
```

### Tests

```
python -m unittest discover -s tests -v
```

### Optional Flask API

```
python app.py
```

| Method | Path                        | Description                                                |
|--------|-----------------------------|--------------------------------------------------------------|
| GET    | `/files`                    | List every file in the origin's catalog                     |
| GET    | `/content/<file_name>`      | Fetch a file's content (or its simulated size, for binaries) |
| POST   | `/files/<file_name>/update` | Bump a file's version, simulating an origin content change   |
| GET    | `/distances/<location>`     | Distance in km from a city to each edge server               |
| GET    | `/analytics`                | Current analytics summary, as JSON                           |
| POST   | `/request`                  | Submit a client request                                      |

```
curl -X POST http://127.0.0.1:5000/request \
  -H "Content-Type: application/json" \
  -d '{"client_name": "Ravi", "location": "Punjab", "file_name": "video.mp4"}'
```

## Project Structure

```
mini-cdn/
├── README.md
├── requirements.txt
├── .gitignore
├── main.py              CLI entry point
├── config.py             topology, coordinates, simulation constants
├── models.py             shared dataclasses (Coordinates, FileObject, Client, Request, ...)
├── network.py            per-server latency + jitter + failure simulation
├── cache.py               LRU cache implementation
├── router.py              distance-based edge selection
├── origin_server.py       file catalog, versioning
├── edge_server.py         cache lookup, staleness check, origin fallback
├── analytics.py           running request statistics
├── logger.py              structured request logging
├── simulator.py           single-request handling + batch event simulation
├── visualizer.py          matplotlib chart generation
├── utils.py               haversine distance, byte formatting
├── app.py                 optional Flask API
├── data/                  origin's file catalog
│   ├── README.md
│   ├── manifest.json
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   ├── product.json
│   └── api-data.json
├── docs/
│   └── architecture.md
└── tests/
    ├── __init__.py
    ├── test_cache.py
    ├── test_network.py
    ├── test_router.py
    ├── test_origin_server.py
    ├── test_edge_server.py
    ├── test_analytics.py
    └── test_simulator.py
```

`logs/` and `docs/charts/` aren't part of the checkout -- both are created automatically the first time you run a simulation or generate charts, and both are gitignored.

## Suggested Commit Sequence

If you're pushing this to your own repository under your own name, this is roughly the order it was actually built in:

1. Initial project scaffolding: config, models, `.gitignore`, requirements
2. Add network latency simulation
3. Implement LRU cache from scratch, with tests
4. Add distance-based routing between edge servers, with tests
5. Add origin server with file catalog and versioning, with tests
6. Add edge server request handling with cache validation, with tests
7. Add request analytics and structured logging, with tests
8. Add batch simulator with event-driven request processing, with tests
9. Add matplotlib visualizations
10. Add CLI entry point
11. Add optional Flask API
12. Add README and architecture docs

## Future Improvements

- Replace the linear nearest-edge scan with a spatial index (k-d tree or geohash) so routing stays fast as the edge fleet grows past a handful of nodes.
- Add TTL-based expiry alongside version checks, so entries can go stale on their own instead of only on an origin update.
- Give failed lookups (file not found, network failure) their own latency instead of reporting 0 ms -- a real round trip still happens even when it ends in an error.
- Support consistent hashing for cache-key distribution across a larger edge fleet, instead of every edge independently caching whatever it happens to serve.
- Persist analytics between runs instead of resetting them every time the process starts.
- Add authentication and rate limiting to the Flask API before it's anything more than a local demo.

## Learning Outcomes

Building this touches a reasonable cross-section of what tends to come up in a systems design interview:

- Geographic routing and the haversine formula
- LRU eviction, and why `OrderedDict` gets you O(1) get/put for free
- Cache coherency -- version-based invalidation vs. TTL, and why this project uses lazy, pull-based invalidation instead of a push/purge API
- Discrete-event simulation with a heap-based priority queue
- Latency modeling: base latency vs. transfer time vs. jitter, and how they compose across two hops on a cache miss
- Structured logging and statistical analysis of system behavior
- Separation of concerns across modules, and custom exceptions scoped to the component that raises them
