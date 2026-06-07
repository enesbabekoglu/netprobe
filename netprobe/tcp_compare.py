"""Güvenilir UDP goodput karşılaştırması için TCP akış taban ölçümü."""

from __future__ import annotations

import json
import socket
import struct
import threading
import time
from pathlib import Path

from .config import DEFAULT_HOST, RECEIVED_DIR
from .metrics import TransferResult, make_transfer_result
from .protocol import new_session_id, safe_filename, sha256_file
from .server import find_free_udp_port


SIZE_HEADER = struct.Struct("!Q")


def _recvall(conn: socket.socket, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining > 0:
        data = conn.recv(remaining)
        if not data:
            raise ConnectionError("connection closed before all bytes were received")
        chunks.append(data)
        remaining -= len(data)
    return b"".join(chunks)


def run_tcp_transfer(
    source: str | Path,
    host: str = DEFAULT_HOST,
    port: int | None = None,
    output_dir: str | Path = RECEIVED_DIR,
) -> TransferResult:
    source_path = Path(source)
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    session_id = new_session_id()
    file_hash = sha256_file(source_path)
    file_size = source_path.stat().st_size
    selected_port = port or find_free_udp_port(host)
    result: dict[str, str] = {}
    ready = threading.Event()

    def server() -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((host, selected_port))
            server_sock.listen(1)
            ready.set()
            conn, _ = server_sock.accept()
            with conn:
                meta_size = SIZE_HEADER.unpack(_recvall(conn, SIZE_HEADER.size))[0]
                metadata = json.loads(_recvall(conn, meta_size).decode("utf-8"))
                destination = output_root / f"{session_id[:8]}_{safe_filename(metadata['file_name'])}"
                remaining = int(metadata["file_size"])
                with destination.open("wb") as handle:
                    while remaining > 0:
                        block = conn.recv(min(64 * 1024, remaining))
                        if not block:
                            raise ConnectionError("client closed while sending file bytes")
                        handle.write(block)
                        remaining -= len(block)
                result["destination_path"] = str(destination)
                result["server_sha256"] = sha256_file(destination)

    thread = threading.Thread(target=server, daemon=True)
    thread.start()
    ready.wait(timeout=2)

    started = time.perf_counter()
    bytes_on_wire = 0
    with socket.create_connection((host, selected_port), timeout=5) as client:
        metadata = json.dumps({"file_name": source_path.name, "file_size": file_size, "sha256": file_hash}).encode(
            "utf-8"
        )
        client.sendall(SIZE_HEADER.pack(len(metadata)))
        client.sendall(metadata)
        bytes_on_wire += SIZE_HEADER.size + len(metadata)
        with source_path.open("rb") as handle:
            for block in iter(lambda: handle.read(64 * 1024), b""):
                client.sendall(block)
                bytes_on_wire += len(block)
    thread.join(timeout=5)
    duration = time.perf_counter() - started

    ok = result.get("server_sha256") == file_hash
    return make_transfer_result(
        session_id=session_id,
        status="success" if ok else "failed",
        protocol="tcp",
        source_path=str(source_path),
        destination_path=result.get("destination_path", ""),
        file_name=source_path.name,
        file_size=file_size,
        sha256=file_hash,
        server_sha256=result.get("server_sha256", ""),
        payload_size=64 * 1024,
        timeout=0,
        window_size=0,
        loss_rate=0,
        total_packets=1,
        data_packets_sent=1,
        retransmissions=0,
        timeouts=0,
        acks_received=1,
        duplicates_seen=0,
        simulated_drops=0,
        bytes_on_wire=bytes_on_wire,
        completion_time=duration,
        rtts=[],
        message="tcp transfer completed" if ok else "tcp sha256 mismatch",
    )
