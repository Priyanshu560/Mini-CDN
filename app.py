"""
Optional Flask API for MiniCDN. This module only translates HTTP
requests into calls against the same Simulator used by the CLI, so
both interfaces stay in sync.

Run with: python app.py
Debug mode is intentionally left off; enable it locally if you need
the reloader, but don't ship a public endpoint with it turned on.
"""

from flask import Flask, jsonify, render_template, request

import config
from main import build_system
from models import Client
from origin_server import OriginFileNotFoundError
from router import InvalidLocationError

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = config.API_MAX_BODY_BYTES
origin, simulator = build_system()


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _bad_request(message):
    return jsonify(error=message), 400


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/meta")
def api_meta():
    return jsonify(
        client_locations=list(config.CLIENT_CITIES.keys()),
        edge_servers=list(config.EDGE_SERVERS.keys()),
    )


@app.get("/files")
def list_files():
    return jsonify(files=origin.list_files())


@app.get("/api/files")
def api_list_files():
    file_list = []
    for name in origin.list_files():
        f = origin.get_file(name)
        file_list.append({
            "name": f.name,
            "version": f.version,
            "size_bytes": f.size_bytes,
            "content_type": f.content_type,
        })
    return jsonify(files=file_list)


@app.get("/content/<file_name>")
def file_content(file_name):
    try:
        file_object = origin.get_file(file_name)
    except OriginFileNotFoundError as error:
        return jsonify(error=str(error)), 404

    if file_object.content:
        return jsonify(
            name=file_object.name,
            content_type=file_object.content_type,
            version=file_object.version,
            content=file_object.content,
        )

    return jsonify(
        name=file_object.name,
        content_type=file_object.content_type,
        version=file_object.version,
        size_bytes=file_object.size_bytes,
        note="Binary content is represented by simulated size only in this project.",
    )


@app.post("/files/<file_name>/update")
@app.post("/api/files/<file_name>/update")
def update_file(file_name):
    try:
        updated = origin.update_file(file_name)
    except OriginFileNotFoundError as error:
        return jsonify(error=str(error)), 404

    return jsonify(name=updated.name, version=updated.version, last_modified=updated.last_modified.isoformat())


@app.get("/api/edges")
def api_edges():
    edge_list = []
    for name, edge in simulator.router.edge_servers.items():
        cached_files = []
        for fname, (cached_copy, size_bytes) in edge.cache._store.items():
            try:
                origin_file = origin.get_file(fname)
                is_stale = (cached_copy.version != origin_file.version)
            except OriginFileNotFoundError:
                is_stale = True
            cached_files.append({
                "name": fname,
                "version": cached_copy.version,
                "size_bytes": size_bytes,
                "is_stale": is_stale,
            })
        edge_list.append({
            "name": edge.name,
            "base_latency_ms": edge.network.base_latency_ms,
            "requests_served": edge.requests_served,
            "cache_utilization": edge.cache.utilization,
            "cache_used_bytes": edge.cache.current_size_bytes,
            "files": cached_files,
        })
    return jsonify(edges=edge_list)


@app.get("/distances/<location>")
def distances(location):
    try:
        return jsonify(simulator.router.distances_from(location))
    except InvalidLocationError as error:
        return jsonify(error=str(error)), 400


@app.get("/analytics")
@app.get("/api/analytics")
def analytics_summary():
    summary = simulator.analytics.summary()
    summary["origin_base_latency_ms"] = config.ORIGIN_BASE_LATENCY_MS
    server_counts = summary.get("requests_per_server", {})
    if server_counts:
        summary["most_used_server"] = max(server_counts, key=server_counts.get)
    else:
        summary["most_used_server"] = None
    return jsonify(summary)


@app.post("/request")
@app.post("/api/request")
def submit_request():
    payload = request.get_json(silent=True)
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        return _bad_request("request body must be a JSON object")

    location = payload.get("location")
    file_name = payload.get("file_name")

    if not location or not file_name:
        return _bad_request("location and file_name are required")

    for field, value in (("location", location), ("file_name", file_name)):
        if not isinstance(value, str):
            return _bad_request(f"{field} must be a string")
        if len(value) > config.API_MAX_FIELD_LENGTH:
            return _bad_request(f"{field} must be at most {config.API_MAX_FIELD_LENGTH} characters")

    client = Client(location=location)
    record = simulator.process_request(client, file_name)

    distance_km = None
    if record.server_name and record.server_name != "-":
        try:
            distance_km = simulator.router.distances_from(location).get(record.server_name)
        except Exception:
            pass

    return jsonify(
        server_selected=record.server_name,
        cache_status=record.cache_status,
        latency_ms=round(record.latency_ms, 2),
        status=record.status,
        distance_km=distance_km,
        file_name=record.file_name,
        location=record.location,
        client_name=payload.get("client_name", "Anonymous"),
        timestamp=record.timestamp.isoformat(),
    )


if __name__ == "__main__":
    app.run(host=config.API_HOST, port=config.API_PORT)
