from __future__ import annotations

import argparse
import socket
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import DEFAULT_HOST, DEFAULT_UDP_PORT, LOG_DIR, RECEIVED_DIR
from .events import EventLogger
from .protocol import (
    Packet,
    PacketType,
    ProtocolError,
    decode_json_payload,
    decode_packet,
    encode_json_packet,
    encode_packet,
    safe_filename,
    sha256_file,
)


@dataclass
class ServerSession:
    session_id: str
    address: tuple[str, int]
    file_name: str
    file_size: int
    expected_sha256: str
    payload_size: int
    total_packets: int
    started_at: float
    chunks: dict[int, bytes] = field(default_factory=dict)
    duplicates: int = 0
    destination_path: Path | None = None
    completed: bool = False


class UDPServer:
    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_UDP_PORT,
        output_dir: str | Path = RECEIVED_DIR,
        log_dir: str | Path = LOG_DIR,
    ) -> None:
        self.host = host
        self.port = port
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = EventLogger(log_dir, "server", "server")
        self.sessions: dict[str, ServerSession] = {}
        self._socket: socket.socket | None = None
        self._stop_event = threading.Event()
        self.completed_sessions = 0

    @property
    def address(self) -> tuple[str, int]:
        if self._socket is None:
            return (self.host, self.port)
        return self._socket.getsockname()[:2]

    def stop(self) -> None:
        self._stop_event.set()
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass

    def start_background(self) -> threading.Thread:
        thread = threading.Thread(target=self.serve_forever, name="netprobe-udp-server", daemon=True)
        thread.start()
        timeout_at = time.perf_counter() + 2
        while self._socket is None and time.perf_counter() < timeout_at:
            time.sleep(0.01)
        return thread

    def serve_forever(self, once: bool = False, idle_timeout: float | None = None) -> None:
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind((self.host, self.port))
        self._socket.settimeout(0.2)
        self.logger.log("server_started", host=self.address[0], port=self.address[1])
        idle_started = time.perf_counter()
        try:
            while not self._stop_event.is_set():
                if once and self.completed_sessions > 0:
                    break
                if idle_timeout is not None and time.perf_counter() - idle_started > idle_timeout:
                    self.logger.log("server_idle_timeout", idle_timeout=idle_timeout)
                    break
                try:
                    datagram, address = self._socket.recvfrom(65_535)
                except socket.timeout:
                    continue
                except OSError:
                    break
                idle_started = time.perf_counter()
                self._handle_datagram(datagram, address)
        finally:
            self.logger.log("server_stopped", completed_sessions=self.completed_sessions)
            if self._socket is not None:
                try:
                    self._socket.close()
                except OSError:
                    pass
                self._socket = None

    def _send(self, datagram: bytes, address: tuple[str, int]) -> None:
        if self._socket is not None:
            self._socket.sendto(datagram, address)

    def _handle_datagram(self, datagram: bytes, address: tuple[str, int]) -> None:
        try:
            packet = decode_packet(datagram)
        except ProtocolError as exc:
            self.logger.log("checksum_failure", address=f"{address[0]}:{address[1]}", error=str(exc))
            return

        if packet.packet_type == PacketType.START:
            self._handle_start(packet, address)
        elif packet.packet_type == PacketType.DATA:
            self._handle_data(packet, address)
        elif packet.packet_type == PacketType.END:
            self._handle_end(packet, address)
        else:
            self.logger.log(
                "unexpected_packet",
                packet_type=packet.packet_type.name,
                session_id=packet.session_id,
                sequence=packet.sequence,
            )

    def _handle_start(self, packet: Packet, address: tuple[str, int]) -> None:
        try:
            metadata = decode_json_payload(packet)
        except ProtocolError as exc:
            self._send_error(packet.session_id, address, str(exc))
            return

        session = ServerSession(
            session_id=packet.session_id,
            address=address,
            file_name=safe_filename(str(metadata.get("file_name", "received.bin"))),
            file_size=int(metadata.get("file_size", 0)),
            expected_sha256=str(metadata.get("sha256", "")),
            payload_size=int(metadata.get("payload_size", 0)),
            total_packets=int(metadata.get("total_packets", packet.total_packets)),
            started_at=time.perf_counter(),
        )
        self.sessions[packet.session_id] = session
        self.logger.log(
            "transfer_started",
            session_id=session.session_id,
            file_name=session.file_name,
            file_size=session.file_size,
            total_packets=session.total_packets,
            peer=f"{address[0]}:{address[1]}",
        )
        self._send_ack(packet.session_id, 0, session.total_packets, address)

    def _handle_data(self, packet: Packet, address: tuple[str, int]) -> None:
        session = self.sessions.get(packet.session_id)
        if session is None:
            self._send_error(packet.session_id, address, "unknown session")
            return

        if packet.sequence in session.chunks:
            session.duplicates += 1
            self.logger.log(
                "duplicate_packet",
                session_id=session.session_id,
                sequence=packet.sequence,
                duplicates=session.duplicates,
            )
            self._send_ack(session.session_id, packet.sequence, session.total_packets, address)
            return

        if packet.sequence >= session.total_packets:
            self._send_error(packet.session_id, address, "sequence exceeds total packet count")
            return

        session.chunks[packet.sequence] = packet.payload
        self.logger.log(
            "packet_received",
            session_id=session.session_id,
            sequence=packet.sequence,
            payload_length=len(packet.payload),
            received_packets=len(session.chunks),
            total_packets=session.total_packets,
        )
        self._send_ack(session.session_id, packet.sequence, session.total_packets, address)

    def _handle_end(self, packet: Packet, address: tuple[str, int]) -> None:
        session = self.sessions.get(packet.session_id)
        if session is None:
            self._send_error(packet.session_id, address, "unknown session")
            return

        missing = sorted(set(range(session.total_packets)) - set(session.chunks))
        if missing:
            message = f"missing packets: {missing[:12]}{'...' if len(missing) > 12 else ''}"
            self.logger.log(
                "transfer_failed",
                session_id=session.session_id,
                reason=message,
                missing_count=len(missing),
            )
            self._send_result(session, address, ok=False, message=message)
            return

        destination = self.output_dir / f"{session.session_id[:8]}_{session.file_name}"
        with destination.open("wb") as handle:
            for sequence in range(session.total_packets):
                handle.write(session.chunks[sequence])

        server_sha256 = sha256_file(destination)
        ok = server_sha256 == session.expected_sha256
        message = "hash verified" if ok else "sha256 mismatch"
        session.destination_path = destination
        session.completed = ok
        if ok:
            self.completed_sessions += 1

        self.logger.log(
            "transfer_completed" if ok else "transfer_failed",
            session_id=session.session_id,
            file_name=session.file_name,
            destination_path=str(destination),
            expected_sha256=session.expected_sha256,
            server_sha256=server_sha256,
            bytes_written=destination.stat().st_size,
            duplicates=session.duplicates,
            completion_time=time.perf_counter() - session.started_at,
            message=message,
        )
        self._send_result(session, address, ok=ok, message=message, server_sha256=server_sha256)

    def _send_ack(self, session_id: str, sequence: int, total_packets: int, address: tuple[str, int]) -> None:
        datagram = encode_packet(PacketType.ACK, session_id, sequence=sequence, total_packets=total_packets)
        self._send(datagram, address)
        self.logger.log("ack_sent", session_id=session_id, sequence=sequence)

    def _send_result(
        self,
        session: ServerSession,
        address: tuple[str, int],
        *,
        ok: bool,
        message: str,
        server_sha256: str = "",
    ) -> None:
        payload: dict[str, Any] = {
            "ok": ok,
            "message": message,
            "server_sha256": server_sha256,
            "destination_path": str(session.destination_path or ""),
            "duplicates": session.duplicates,
            "received_packets": len(session.chunks),
            "total_packets": session.total_packets,
        }
        self._send(encode_json_packet(PacketType.RESULT, session.session_id, payload), address)
        self.logger.log("result_sent", session_id=session.session_id, ok=ok, message=message)

    def _send_error(self, session_id: str, address: tuple[str, int], message: str) -> None:
        self._send(encode_json_packet(PacketType.ERROR, session_id, {"message": message}), address)
        self.logger.log("error_sent", session_id=session_id, message=message)


def find_free_udp_port(host: str = DEFAULT_HOST) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the NetProbe UDP server")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_UDP_PORT)
    parser.add_argument("--output-dir", default=str(RECEIVED_DIR))
    parser.add_argument("--log-dir", default=str(LOG_DIR))
    parser.add_argument("--once", action="store_true", help="stop after the first successful transfer")
    parser.add_argument("--idle-timeout", type=float, default=None)
    args = parser.parse_args()

    server = UDPServer(args.host, args.port, args.output_dir, args.log_dir)
    try:
        server.serve_forever(once=args.once, idle_timeout=args.idle_timeout)
    except KeyboardInterrupt:
        server.stop()


if __name__ == "__main__":
    main()
