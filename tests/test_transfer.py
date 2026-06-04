from __future__ import annotations

import socket
import threading

from netprobe.client import send_file
from netprobe.config import TransferConfig
from netprobe.protocol import (
    PacketType,
    decode_json_payload,
    decode_packet,
    encode_json_packet,
    encode_packet,
    new_session_id,
    sha256_file,
)
from netprobe.server import UDPServer, find_free_udp_port


def _start_server(tmp_path):
    port = find_free_udp_port()
    server = UDPServer("127.0.0.1", port, output_dir=tmp_path / "received", log_dir=tmp_path / "logs")
    thread = server.start_background()
    return server, thread, port


def _stop_server(server: UDPServer, thread: threading.Thread) -> None:
    server.stop()
    thread.join(timeout=2)


def test_reliable_udp_transfer_success(tmp_path) -> None:
    source = tmp_path / "payload.bin"
    source.write_bytes(bytes(range(256)) * 8)
    server, thread, port = _start_server(tmp_path)
    try:
        result = send_file(
            source,
            TransferConfig(
                host="127.0.0.1",
                port=port,
                payload_size=256,
                timeout=0.1,
                max_retries=5,
                window_size=4,
                log_dir=tmp_path / "client_logs",
            ),
        )
    finally:
        _stop_server(server, thread)

    assert result.status == "success"
    assert result.sha256 == result.server_sha256
    assert result.acks_received == result.total_packets
    assert sha256_file(result.destination_path) == sha256_file(source)


def test_simulated_loss_recovers_with_retransmission(tmp_path) -> None:
    source = tmp_path / "loss.bin"
    source.write_bytes(b"network-loss" * 500)
    server, thread, port = _start_server(tmp_path)
    try:
        result = send_file(
            source,
            TransferConfig(
                host="127.0.0.1",
                port=port,
                payload_size=128,
                timeout=0.04,
                max_retries=12,
                window_size=6,
                loss_rate=0.2,
                seed=4,
                log_dir=tmp_path / "client_logs",
            ),
        )
    finally:
        _stop_server(server, thread)

    assert result.status == "success"
    assert result.simulated_drops > 0
    assert result.retransmissions > 0
    assert result.sha256 == result.server_sha256


def test_max_retry_failure_is_reported(tmp_path) -> None:
    source = tmp_path / "never-arrives.bin"
    source.write_bytes(b"x" * 1024)
    server, thread, port = _start_server(tmp_path)
    try:
        result = send_file(
            source,
            TransferConfig(
                host="127.0.0.1",
                port=port,
                payload_size=256,
                timeout=0.02,
                max_retries=1,
                window_size=2,
                loss_rate=1.0,
                seed=1,
                log_dir=tmp_path / "client_logs",
            ),
        )
    finally:
        _stop_server(server, thread)

    assert result.status == "failed"
    assert "exceeded max retry" in result.message


def test_duplicate_packet_is_not_written_twice(tmp_path) -> None:
    source_payload = b"duplicate-check"
    session_id = new_session_id()
    server, thread, port = _start_server(tmp_path)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(1)
            metadata = {
                "file_name": "dup.bin",
                "file_size": len(source_payload),
                "sha256": sha256_file(_write_temp_payload(tmp_path, source_payload)),
                "payload_size": len(source_payload),
                "total_packets": 1,
                "window_size": 1,
            }
            sock.sendto(encode_json_packet(PacketType.START, session_id, metadata, total_packets=1), ("127.0.0.1", port))
            assert decode_packet(sock.recvfrom(65_535)[0]).packet_type == PacketType.ACK

            data = encode_packet(PacketType.DATA, session_id, sequence=0, total_packets=1, payload=source_payload)
            sock.sendto(data, ("127.0.0.1", port))
            assert decode_packet(sock.recvfrom(65_535)[0]).packet_type == PacketType.ACK
            sock.sendto(data, ("127.0.0.1", port))
            assert decode_packet(sock.recvfrom(65_535)[0]).packet_type == PacketType.ACK

            sock.sendto(encode_json_packet(PacketType.END, session_id, {"sha256": metadata["sha256"]}, total_packets=1), ("127.0.0.1", port))
            result = decode_json_payload(decode_packet(sock.recvfrom(65_535)[0]))
    finally:
        _stop_server(server, thread)

    assert result["ok"] is True
    assert server.sessions[session_id].duplicates == 1
    assert server.sessions[session_id].destination_path.read_bytes() == source_payload


def _write_temp_payload(tmp_path, payload: bytes):
    path = tmp_path / "source.bin"
    path.write_bytes(payload)
    return path
