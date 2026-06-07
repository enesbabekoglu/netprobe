"""Seçici tekrarlı kayan pencere ve yeniden gönderimli güvenilir UDP istemcisi."""

from __future__ import annotations

import argparse
import socket
import time
from pathlib import Path

from .config import DEFAULT_HOST, DEFAULT_UDP_PORT, LOG_DIR, TransferConfig
from .events import EventLogger
from .metrics import TransferResult, make_transfer_result
from .protocol import (
    HEADER,
    PacketType,
    ProtocolError,
    decode_json_payload,
    decode_packet,
    encode_json_packet,
    encode_packet,
    new_session_id,
    sha256_file,
    split_file,
)
from .simulator import NetworkSimulator


class ReliableUDPClient:
    def __init__(self, config: TransferConfig) -> None:
        config.validate()
        self.config = config

    def send_file(self, source: str | Path) -> TransferResult:
        source_path = Path(source)
        if not source_path.exists() or not source_path.is_file():
            raise FileNotFoundError(source_path)

        session_id = new_session_id()
        logger = EventLogger(self.config.log_dir, f"client_{session_id[:8]}", "client")
        simulator = NetworkSimulator(
            loss_rate=self.config.loss_rate,
            delay_ms=self.config.delay_ms,
            jitter_ms=self.config.jitter_ms,
            seed=self.config.seed,
        )
        chunks = split_file(source_path, self.config.payload_size)
        total_packets = len(chunks)
        file_size = source_path.stat().st_size
        file_hash = sha256_file(source_path)
        metrics = {
            "data_packets_sent": 0,
            "retransmissions": 0,
            "timeouts": 0,
            "acks_received": 0,
            "duplicates_seen": 0,
            "simulated_drops": 0,
            "bytes_on_wire": 0,
        }
        rtts: list[float] = []
        started = time.perf_counter()

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(min(0.05, self.config.timeout))
            peer = (self.config.host, self.config.port)
            logger.log(
                "client_started",
                session_id=session_id,
                file_name=source_path.name,
                file_size=file_size,
                total_packets=total_packets,
                payload_size=self.config.payload_size,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
                window_size=self.config.window_size,
                loss_rate=self.config.loss_rate,
                peer=f"{peer[0]}:{peer[1]}",
            )

            metadata = {
                "file_name": source_path.name,
                "file_size": file_size,
                "sha256": file_hash,
                "payload_size": self.config.payload_size,
                "total_packets": total_packets,
                "window_size": self.config.window_size,
            }
            start_packet = encode_json_packet(PacketType.START, session_id, metadata, total_packets=total_packets)
            if not self._send_control_and_wait_for_ack(sock, peer, logger, start_packet, session_id, "START"):
                return self._finish(
                    session_id,
                    "failed",
                    source_path,
                    file_hash,
                    total_packets,
                    metrics,
                    rtts,
                    started,
                    "START packet was not acknowledged",
                )

            # Kayan pencere: base = en eski onaysız seq, next_sequence = gönderilecek sıradaki seq
            acked: set[int] = set()
            sent_at: dict[int, float] = {}
            retry_count: dict[int, int] = {sequence: 0 for sequence in range(total_packets)}
            base = 0
            next_sequence = 0

            while len(acked) < total_packets:
                while next_sequence < total_packets and next_sequence < base + self.config.window_size:
                    self._send_data_packet(
                        sock,
                        peer,
                        logger,
                        simulator,
                        session_id,
                        next_sequence,
                        total_packets,
                        chunks[next_sequence],
                        metrics,
                        sent_at,
                        retransmission=False,
                    )
                    next_sequence += 1

                now = time.perf_counter()
                try:
                    datagram, _ = sock.recvfrom(65_535)
                    packet = decode_packet(datagram)
                except socket.timeout:
                    packet = None
                except ProtocolError as exc:
                    logger.log("checksum_failure", error=str(exc))
                    packet = None

                if packet is not None and packet.session_id == session_id:
                    if packet.packet_type == PacketType.ACK:
                        if packet.sequence in acked:
                            metrics["duplicates_seen"] += 1
                            logger.log("duplicate_ack", session_id=session_id, sequence=packet.sequence)
                        else:
                            acked.add(packet.sequence)
                            metrics["acks_received"] += 1
                            if packet.sequence in sent_at:
                                rtts.append(time.perf_counter() - sent_at[packet.sequence])
                            logger.log(
                                "ack_received",
                                session_id=session_id,
                                sequence=packet.sequence,
                                acked_packets=len(acked),
                                total_packets=total_packets,
                            )
                            while base in acked:
                                base += 1
                    elif packet.packet_type == PacketType.ERROR:
                        error_payload = decode_json_payload(packet)
                        return self._finish(
                            session_id,
                            "failed",
                            source_path,
                            file_hash,
                            total_packets,
                            metrics,
                            rtts,
                            started,
                            str(error_payload.get("message", "server error")),
                        )

                # Yapılandırılan timeout'u aşan uçuştaki paketleri yeniden gönder
                now = time.perf_counter()
                for sequence in range(base, min(next_sequence, total_packets)):
                    if sequence in acked:
                        continue
                    if now - sent_at.get(sequence, now) < self.config.timeout:
                        continue

                    metrics["timeouts"] += 1
                    logger.log(
                        "timeout",
                        session_id=session_id,
                        sequence=sequence,
                        retries=retry_count[sequence],
                        max_retries=self.config.max_retries,
                    )
                    if retry_count[sequence] >= self.config.max_retries:
                        message = f"packet {sequence} exceeded max retry limit ({self.config.max_retries})"
                        logger.log("transfer_failed", session_id=session_id, sequence=sequence, message=message)
                        return self._finish(
                            session_id,
                            "failed",
                            source_path,
                            file_hash,
                            total_packets,
                            metrics,
                            rtts,
                            started,
                            message,
                        )
                    retry_count[sequence] += 1
                    self._send_data_packet(
                        sock,
                        peer,
                        logger,
                        simulator,
                        session_id,
                        sequence,
                        total_packets,
                        chunks[sequence],
                        metrics,
                        sent_at,
                        retransmission=True,
                    )

            result_payload = self._send_end_and_wait_for_result(
                sock,
                peer,
                logger,
                session_id,
                total_packets,
                file_hash,
                file_size,
            )
            if not result_payload.get("ok"):
                return self._finish(
                    session_id,
                    "failed",
                    source_path,
                    file_hash,
                    total_packets,
                    metrics,
                    rtts,
                    started,
                    str(result_payload.get("message", "server did not verify the transfer")),
                    server_sha256=str(result_payload.get("server_sha256", "")),
                    destination_path=str(result_payload.get("destination_path", "")),
                )

            logger.log(
                "transfer_completed",
                session_id=session_id,
                destination_path=str(result_payload.get("destination_path", "")),
                server_sha256=str(result_payload.get("server_sha256", "")),
                completion_time=time.perf_counter() - started,
            )
            return self._finish(
                session_id,
                "success",
                source_path,
                file_hash,
                total_packets,
                metrics,
                rtts,
                started,
                "transfer completed and sha256 verified",
                server_sha256=str(result_payload.get("server_sha256", "")),
                destination_path=str(result_payload.get("destination_path", "")),
            )

    def _send_control_and_wait_for_ack(
        self,
        sock: socket.socket,
        peer: tuple[str, int],
        logger: EventLogger,
        datagram: bytes,
        session_id: str,
        label: str,
    ) -> bool:
        for attempt in range(self.config.max_retries + 1):
            sock.sendto(datagram, peer)
            logger.log("packet_sent", packet_type=label, session_id=session_id, attempt=attempt)
            deadline = time.perf_counter() + self.config.timeout
            while time.perf_counter() < deadline:
                try:
                    raw, _ = sock.recvfrom(65_535)
                    packet = decode_packet(raw)
                except socket.timeout:
                    continue
                except ProtocolError as exc:
                    logger.log("checksum_failure", packet_type=label, error=str(exc))
                    continue
                if packet.session_id == session_id and packet.packet_type == PacketType.ACK:
                    logger.log("ack_received", packet_type=label, session_id=session_id, sequence=packet.sequence)
                    return True
            logger.log("timeout", packet_type=label, session_id=session_id, attempt=attempt)
        return False

    def _send_data_packet(
        self,
        sock: socket.socket,
        peer: tuple[str, int],
        logger: EventLogger,
        simulator: NetworkSimulator,
        session_id: str,
        sequence: int,
        total_packets: int,
        payload: bytes,
        metrics: dict[str, int],
        sent_at: dict[int, float],
        *,
        retransmission: bool,
    ) -> None:
        datagram = encode_packet(PacketType.DATA, session_id, sequence, total_packets, payload)
        simulator.apply_delay()
        if simulator.should_drop():
            metrics["simulated_drops"] += 1
            sent_at[sequence] = time.perf_counter()
            logger.log(
                "packet_dropped_simulated",
                session_id=session_id,
                sequence=sequence,
                retransmission=retransmission,
                loss_rate=self.config.loss_rate,
            )
            return

        sock.sendto(datagram, peer)
        sent_at[sequence] = time.perf_counter()
        metrics["data_packets_sent"] += 1
        metrics["bytes_on_wire"] += len(datagram)
        if retransmission:
            metrics["retransmissions"] += 1
        logger.log(
            "packet_sent",
            packet_type="DATA",
            session_id=session_id,
            sequence=sequence,
            payload_length=len(payload),
            datagram_length=len(datagram),
            retransmission=retransmission,
        )

    def _send_end_and_wait_for_result(
        self,
        sock: socket.socket,
        peer: tuple[str, int],
        logger: EventLogger,
        session_id: str,
        total_packets: int,
        file_hash: str,
        file_size: int,
    ) -> dict[str, object]:
        end_packet = encode_json_packet(
            PacketType.END,
            session_id,
            {"sha256": file_hash, "file_size": file_size},
            total_packets=total_packets,
        )
        for attempt in range(self.config.max_retries + 1):
            sock.sendto(end_packet, peer)
            logger.log("packet_sent", packet_type="END", session_id=session_id, attempt=attempt)
            deadline = time.perf_counter() + self.config.timeout
            while time.perf_counter() < deadline:
                try:
                    raw, _ = sock.recvfrom(65_535)
                    packet = decode_packet(raw)
                except socket.timeout:
                    continue
                except ProtocolError as exc:
                    logger.log("checksum_failure", packet_type="RESULT", error=str(exc))
                    continue
                if packet.session_id != session_id:
                    continue
                if packet.packet_type == PacketType.RESULT:
                    result = decode_json_payload(packet)
                    logger.log("result_received", session_id=session_id, **result)
                    return result
                if packet.packet_type == PacketType.ERROR:
                    result = decode_json_payload(packet)
                    logger.log("error_received", session_id=session_id, **result)
                    return {"ok": False, **result}
            logger.log("timeout", packet_type="END", session_id=session_id, attempt=attempt)
        return {"ok": False, "message": "END packet was not acknowledged with RESULT"}

    def _finish(
        self,
        session_id: str,
        status: str,
        source_path: Path,
        sha256: str,
        total_packets: int,
        metrics: dict[str, int],
        rtts: list[float],
        started: float,
        message: str,
        *,
        server_sha256: str = "",
        destination_path: str = "",
    ) -> TransferResult:
        return make_transfer_result(
            session_id=session_id,
            status=status,
            protocol="reliable_udp",
            source_path=str(source_path),
            destination_path=destination_path,
            file_name=source_path.name,
            file_size=source_path.stat().st_size,
            sha256=sha256,
            server_sha256=server_sha256,
            payload_size=self.config.payload_size,
            timeout=self.config.timeout,
            window_size=self.config.window_size,
            loss_rate=self.config.loss_rate,
            total_packets=total_packets,
            data_packets_sent=metrics["data_packets_sent"],
            retransmissions=metrics["retransmissions"],
            timeouts=metrics["timeouts"],
            acks_received=metrics["acks_received"],
            duplicates_seen=metrics["duplicates_seen"],
            simulated_drops=metrics["simulated_drops"],
            bytes_on_wire=metrics["bytes_on_wire"],
            completion_time=time.perf_counter() - started,
            rtts=rtts,
            message=message,
        )


def send_file(source: str | Path, config: TransferConfig) -> TransferResult:
    return ReliableUDPClient(config).send_file(source)


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a file through the NetProbe reliable UDP client")
    subparsers = parser.add_subparsers(dest="command", required=True)
    send_parser = subparsers.add_parser("send", help="send a file to a NetProbe UDP server")
    send_parser.add_argument("file")
    send_parser.add_argument("--host", default=DEFAULT_HOST)
    send_parser.add_argument("--port", type=int, default=DEFAULT_UDP_PORT)
    send_parser.add_argument("--payload-size", type=int, default=1024)
    send_parser.add_argument("--timeout", type=float, default=0.5)
    send_parser.add_argument("--max-retries", type=int, default=5)
    send_parser.add_argument("--window-size", type=int, default=8)
    send_parser.add_argument("--loss-rate", type=float, default=0.0)
    send_parser.add_argument("--delay-ms", type=float, default=0.0)
    send_parser.add_argument("--log-dir", default=str(LOG_DIR))
    args = parser.parse_args()

    if args.command == "send":
        config = TransferConfig(
            host=args.host,
            port=args.port,
            payload_size=args.payload_size,
            timeout=args.timeout,
            max_retries=args.max_retries,
            window_size=args.window_size,
            loss_rate=args.loss_rate,
            delay_ms=args.delay_ms,
            log_dir=Path(args.log_dir),
        )
        result = send_file(args.file, config)
        print(f"status={result.status}")
        print(f"session={result.session_id}")
        print(f"file={result.file_name} bytes={result.file_size}")
        print(f"sha256={result.sha256}")
        print(f"server_sha256={result.server_sha256}")
        print(f"destination={result.destination_path}")
        print(f"completion_time={result.completion_time:.4f}s")
        print(f"throughput={result.throughput_bps / 1_000_000:.3f} Mbps")
        print(f"goodput={result.goodput_bps / 1_000_000:.3f} Mbps")
        print(f"retransmissions={result.retransmissions} timeouts={result.timeouts}")
        print(f"message={result.message}")
        raise SystemExit(0 if result.status == "success" else 2)


if __name__ == "__main__":
    main()
