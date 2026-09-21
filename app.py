"""
Optional Flask API for MiniCDN. This module only translates HTTP
requests into calls against the same Simulator used by the CLI, so
both interfaces stay in sync.

Run with: python app.py
Debug mode is intentionally left off; enable it locally if you need
the reloader, but don't ship a public endpoint with it turned on.
"""

from flask import Flask, jsonify, request, send_from_directory

from main import build_system
from models import Client
from origin_server import OriginFileNotFoundError
from router import InvalidLocationError

app = Flask(__name__)
origin, simulator = build_system()


@app.get("/")
def dashboard():
    return send_from_directory("data", "index.html")


@app.get("/style.css")
def dashboard_css():
    return send_from_directory("data", "style.css")


@app.get("/script.js")
def dashboard_js():
    return send_from_directory("data", "script.js")


@app.get("/files")
def list_files():
    return jsonify(files=origin.list_files())


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
def update_file(file_name):
    try:
        updated = origin.update_file(file_name)
    except OriginFileNotFoundError as error:
        return jsonify(error=str(error)), 404

    return jsonify(name=updated.name, version=updated.version, last_modified=updated.last_modified.isoformat())


@app.get("/distances/<location>")
def distances(location):
    try:
        return jsonify(simulator.router.distances_from(location))
    except InvalidLocationError as error:
        return jsonify(error=str(error)), 400


@app.get("/analytics")
def analytics_summary():
    return jsonify(simulator.analytics.summary())


@app.post("/request")
def submit_request():
    payload = request.get_json(silent=True) or {}
    client_name = payload.get("client_name", "Anonymous")
    location = payload.get("location")
    file_name = payload.get("file_name")

    if not location or not file_name:
        return jsonify(error="location and file_name are required"), 400

    client = Client(name=client_name, location=location)
    record = simulator.process_request(client, file_name)

    return jsonify(
        server_selected=record.server_name,
        cache_status=record.cache_status,
        latency_ms=round(record.latency_ms, 2),
        status=record.status,
    )


if __name__ == "__main__":
    app.run(port=5000)
