from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_sock import Sock

from .analysis import build_analysis
from .client import send_file
from .config import DATA_DIR, LOG_DIR, OUTPUT_DIR, PROJECT_ROOT, TransferConfig
from .events import read_recent_events
from .experiments import run_experiments
from .protocol import safe_filename
from .sample_data import ensure_sample_files
from .server import UDPServer, find_free_udp_port


WEB_ROOT = PROJECT_ROOT / "web"
UPLOAD_DIR = DATA_DIR / "uploaded_files"


class WebServerManager:
    def __init__(self) -> None:
        self.port = find_free_udp_port()
        self.server = UDPServer(
            host="127.0.0.1",
            port=self.port,
            output_dir=OUTPUT_DIR / "web_received",
            log_dir=OUTPUT_DIR / "logs" / "web_server",
        )
        self.thread = self.server.start_background()

    def stop(self) -> None:
        self.server.stop()
        self.thread.join(timeout=2)


manager: WebServerManager | None = None


def build_status_payload() -> dict[str, Any]:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    files = [*ensure_sample_files(), *sorted(path for path in UPLOAD_DIR.glob("*") if path.is_file())]
    samples = [
        {
            "name": path.name,
            "path": str(path),
            "size": path.stat().st_size,
            "kind": "uploaded" if path.parent == UPLOAD_DIR else "sample",
        }
        for path in files
    ]
    event_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for event in [*read_recent_events(OUTPUT_DIR / "logs", limit=220), *read_recent_events(LOG_DIR, limit=80)]:
        key = (
            str(event.get("timestamp", "")),
            str(event.get("role", "")),
            str(event.get("event", "")),
        )
        event_by_key[key] = event
    events = sorted(event_by_key.values(), key=lambda row: float(row.get("monotonic", 0.0)))[-180:]
    charts = []
    chart_root = OUTPUT_DIR / "analysis" / "charts"
    if chart_root.exists():
        charts = [
            {
                "name": path.name,
                "url": f"/outputs/analysis/charts/{path.name}",
                "mtime": path.stat().st_mtime,
            }
            for path in sorted([*chart_root.glob("*.svg"), *chart_root.glob("*.png")])
        ]
    results_path = OUTPUT_DIR / "experiments" / "results.csv"
    return {
        "server": {
            "host": "127.0.0.1",
            "port": manager.port if manager else None,
            "running": manager is not None,
        },
        "samples": samples,
        "events": events,
        "charts": charts,
        "results_exists": results_path.exists(),
        "report_path": str(PROJECT_ROOT / "docs" / "rapor-taslagi.md"),
        "deliverable_path": str(PROJECT_ROOT / "dist" / "netprobe-deliverable.zip"),
        "updated_at": time.time(),
    }


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(WEB_ROOT / "templates"),
        static_folder=str(WEB_ROOT / "static"),
        static_url_path="/static",
    )
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
    sock = Sock(app)

    @app.get("/")
    def index():
        return render_template("index.html", asset_version=int(time.time()))

    @app.get("/api/status")
    def status():
        return jsonify(build_status_payload())

    @sock.route("/ws/events")
    def event_stream(ws):
        last_signature = ""
        while True:
            payload = build_status_payload()
            signature = json.dumps(
                {
                    "event_count": len(payload["events"]),
                    "last_event": payload["events"][-1] if payload["events"] else None,
                    "charts": [(chart["name"], chart["mtime"]) for chart in payload["charts"]],
                    "server": payload["server"],
                },
                sort_keys=True,
                ensure_ascii=False,
            )
            if signature != last_signature:
                ws.send(json.dumps({"type": "status", "payload": payload}, ensure_ascii=False))
                last_signature = signature
            time.sleep(0.35)

    @app.post("/api/transfer")
    def transfer():
        payload: dict[str, Any] = request.get_json(force=True, silent=True) or {}
        sample_name = str(payload.get("sample", "small_16kb.bin"))
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        sample_map = {
            path.name: path
            for path in [*ensure_sample_files(), *sorted(path for path in UPLOAD_DIR.glob("*") if path.is_file())]
        }
        source = sample_map.get(sample_name)
        if source is None:
            return jsonify({"ok": False, "message": f"Bilinmeyen örnek dosya: {sample_name}"}), 400
        if manager is None:
            return jsonify({"ok": False, "message": "Gömülü UDP sunucusu çalışmıyor"}), 500

        config = TransferConfig(
            host="127.0.0.1",
            port=manager.port,
            payload_size=int(payload.get("payload_size", 1024)),
            timeout=float(payload.get("timeout", 0.5)),
            max_retries=int(payload.get("max_retries", 5)),
            window_size=int(payload.get("window_size", 8)),
            loss_rate=float(payload.get("loss_rate", 0.0)),
            delay_ms=float(payload.get("delay_ms", 0.0)),
            log_dir=OUTPUT_DIR / "logs" / "web_client",
        )
        result = send_file(source, config)
        return jsonify({"ok": result.status == "success", "result": result.to_dict()})

    @app.post("/api/upload")
    def upload():
        uploaded = request.files.get("file")
        if uploaded is None or not uploaded.filename:
            return jsonify({"ok": False, "message": "Dosya alanı zorunludur"}), 400
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        file_name = safe_filename(uploaded.filename)
        destination = UPLOAD_DIR / file_name
        counter = 1
        while destination.exists():
            destination = UPLOAD_DIR / f"{destination.stem}_{counter}{destination.suffix}"
            counter += 1
        uploaded.save(destination)
        return jsonify(
            {
                "ok": True,
                "file": {
                    "name": destination.name,
                    "path": str(destination),
                    "size": destination.stat().st_size,
                    "kind": "uploaded",
                },
            }
        )

    @app.post("/api/experiments")
    def experiments():
        payload: dict[str, Any] = request.get_json(force=True, silent=True) or {}
        profile = str(payload.get("profile", "quick"))
        path = run_experiments(profile=profile, output_dir=OUTPUT_DIR)
        return jsonify({"ok": True, "results_path": str(path)})

    @app.post("/api/analysis")
    def analysis():
        path = build_analysis(OUTPUT_DIR)
        return jsonify({"ok": True, "summary_path": str(path)})

    @app.get("/outputs/<path:filename>")
    def outputs(filename: str):
        return send_from_directory(OUTPUT_DIR, filename)

    @app.get("/docs/<path:filename>")
    def docs(filename: str):
        return send_from_directory(PROJECT_ROOT / "docs", filename)

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the NetProbe web dashboard")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    ensure_sample_files()
    global manager
    manager = WebServerManager()
    app = create_app()
    try:
        app.run(host=args.host, port=args.port, debug=args.debug, use_reloader=False, threaded=True)
    finally:
        manager.stop()
        manager = None


if __name__ == "__main__":
    main()
