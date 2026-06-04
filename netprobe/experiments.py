from __future__ import annotations

import argparse
import csv
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .analysis import build_analysis
from .client import send_file
from .config import DEFAULT_HOST, OUTPUT_DIR, TransferConfig
from .sample_data import ensure_sample_files
from .server import UDPServer, find_free_udp_port
from .tcp_compare import run_tcp_transfer


@dataclass(frozen=True)
class ExperimentCase:
    scenario: str
    label: str
    source: Path
    payload_size: int = 1024
    timeout: float = 0.5
    window_size: int = 8
    loss_rate: float = 0.0
    seed: int = 42


def build_cases(profile: str, sample_dir: str | Path | None = None) -> list[ExperimentCase]:
    samples = {path.name: path for path in ensure_sample_files(sample_dir or Path("data/sample_files"))}
    small = samples["small_16kb.bin"]
    medium = samples["medium_128kb.bin"]
    large = samples["large_512kb.bin"]

    payload_values = [512, 1024, 2048, 4096]
    timeout_values = [0.2, 0.5, 1.0, 1.5]
    loss_values = [0.0, 0.02, 0.05, 0.10]
    file_cases = [small, medium, large]

    if profile == "quick":
        file_for_param = small
    else:
        file_for_param = medium

    cases: list[ExperimentCase] = []
    cases.extend(
        ExperimentCase("packet_size", f"payload={value}", file_for_param, payload_size=value, timeout=0.3, seed=100 + value)
        for value in payload_values
    )
    cases.extend(
        ExperimentCase("timeout", f"timeout={value}", file_for_param, timeout=value, loss_rate=0.05, seed=200 + index)
        for index, value in enumerate(timeout_values)
    )
    cases.extend(
        ExperimentCase("loss_rate", f"loss={value:.0%}", file_for_param, timeout=0.3, loss_rate=value, seed=300 + index)
        for index, value in enumerate(loss_values)
    )
    cases.extend(
        ExperimentCase("file_size", source.name, source, timeout=0.3, seed=400 + index)
        for index, source in enumerate(file_cases)
    )
    if profile == "quick":
        return cases

    cases.append(ExperimentCase("stop_and_wait", "window=1", medium, window_size=1, timeout=0.3, seed=501))
    cases.append(ExperimentCase("sliding_window", "window=8", medium, window_size=8, timeout=0.3, seed=502))
    return cases


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fields = sorted({key for row in rows for key in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run_experiments(
    *,
    profile: str = "quick",
    output_dir: str | Path = OUTPUT_DIR,
    host: str = DEFAULT_HOST,
    run_analysis: bool = True,
) -> Path:
    root = Path(output_dir)
    experiment_dir = root / "experiments"
    received_dir = root / "received"
    client_log_dir = root / "logs" / "client"
    server_log_dir = root / "logs" / "server"
    for directory in [experiment_dir, received_dir, client_log_dir, server_log_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    sample_dir = root / "sample_files"
    cases = build_cases(profile, sample_dir)
    port = find_free_udp_port(host)
    server = UDPServer(host=host, port=port, output_dir=received_dir, log_dir=server_log_dir)
    server_thread = server.start_background()
    rows: list[dict[str, object]] = []

    try:
        for index, case in enumerate(cases, start=1):
            config = TransferConfig(
                host=host,
                port=port,
                payload_size=case.payload_size,
                timeout=case.timeout,
                window_size=case.window_size,
                max_retries=5,
                loss_rate=case.loss_rate,
                seed=case.seed,
                log_dir=client_log_dir,
            )
            result = send_file(case.source, config)
            row = result.to_dict()
            row.update(
                {
                    "case_id": index,
                    "scenario": case.scenario,
                    "label": case.label,
                    "profile": profile,
                    "source_sample": case.source.name,
                }
            )
            rows.append(row)
            time.sleep(0.03)

        tcp_source = ensure_sample_files(sample_dir)[1]
        tcp_result = run_tcp_transfer(tcp_source, host=host, output_dir=received_dir)
        tcp_row = tcp_result.to_dict()
        tcp_row.update(
            {
                "case_id": len(rows) + 1,
                "scenario": "tcp_compare",
                "label": "TCP baseline",
                "profile": profile,
                "source_sample": tcp_source.name,
            }
        )
        rows.append(tcp_row)
    finally:
        server.stop()
        server_thread.join(timeout=2)

    csv_path = experiment_dir / "results.csv"
    json_path = experiment_dir / "results.json"
    _write_rows(csv_path, rows)
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    if run_analysis:
        build_analysis(output_dir=root)
    return csv_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run NetProbe comparative experiments")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="run the experiment matrix")
    run_parser.add_argument("--profile", choices=["quick", "full"], default="quick")
    run_parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    run_parser.add_argument("--skip-analysis", action="store_true")
    args = parser.parse_args()

    if args.command == "run":
        path = run_experiments(profile=args.profile, output_dir=args.output_dir, run_analysis=not args.skip_analysis)
        print(f"results written to {path}")


if __name__ == "__main__":
    main()
