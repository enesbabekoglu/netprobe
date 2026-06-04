from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class TransferResult:
    session_id: str
    status: str
    protocol: str
    source_path: str
    destination_path: str
    file_name: str
    file_size: int
    sha256: str
    server_sha256: str
    payload_size: int
    timeout: float
    window_size: int
    loss_rate: float
    total_packets: int
    data_packets_sent: int
    retransmissions: int
    timeouts: int
    acks_received: int
    duplicates_seen: int
    simulated_drops: int
    bytes_on_wire: int
    completion_time: float
    throughput_bps: float
    goodput_bps: float
    packet_loss_rate: float
    retransmission_rate: float
    avg_rtt_ms: float
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        row = asdict(self)
        row["throughput_mbps"] = self.throughput_bps / 1_000_000
        row["goodput_mbps"] = self.goodput_bps / 1_000_000
        row["completion_time_ms"] = self.completion_time * 1000
        return row


def make_transfer_result(
    *,
    session_id: str,
    status: str,
    protocol: str,
    source_path: str,
    destination_path: str = "",
    file_name: str,
    file_size: int,
    sha256: str,
    server_sha256: str = "",
    payload_size: int,
    timeout: float,
    window_size: int,
    loss_rate: float,
    total_packets: int,
    data_packets_sent: int,
    retransmissions: int,
    timeouts: int,
    acks_received: int,
    duplicates_seen: int,
    simulated_drops: int,
    bytes_on_wire: int,
    completion_time: float,
    rtts: list[float] | None = None,
    message: str = "",
) -> TransferResult:
    duration = max(completion_time, 1e-9)
    throughput_bps = (bytes_on_wire * 8) / duration
    goodput_bps = ((file_size if status == "success" else 0) * 8) / duration
    attempted_data = data_packets_sent + simulated_drops
    packet_loss_rate = simulated_drops / attempted_data if attempted_data else 0.0
    retransmission_rate = retransmissions / total_packets if total_packets else 0.0
    avg_rtt_ms = (sum(rtts or []) / len(rtts or [1])) * 1000 if rtts else 0.0
    return TransferResult(
        session_id=session_id,
        status=status,
        protocol=protocol,
        source_path=source_path,
        destination_path=destination_path,
        file_name=file_name,
        file_size=file_size,
        sha256=sha256,
        server_sha256=server_sha256,
        payload_size=payload_size,
        timeout=timeout,
        window_size=window_size,
        loss_rate=loss_rate,
        total_packets=total_packets,
        data_packets_sent=data_packets_sent,
        retransmissions=retransmissions,
        timeouts=timeouts,
        acks_received=acks_received,
        duplicates_seen=duplicates_seen,
        simulated_drops=simulated_drops,
        bytes_on_wire=bytes_on_wire,
        completion_time=completion_time,
        throughput_bps=throughput_bps,
        goodput_bps=goodput_bps,
        packet_loss_rate=packet_loss_rate,
        retransmission_rate=retransmission_rate,
        avg_rtt_ms=avg_rtt_ms,
        message=message,
    )
