"""NetProbe kablo formatı: ikili paket başlığı, CRC32 checksum ve dosya yardımcıları."""

from __future__ import annotations

import enum
import hashlib
import json
import re
import struct
import uuid
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MAGIC = b"NTPB"
VERSION = 1
# Başlık alanları: magic(4) sürüm(1) tip(1) bayrak(2) oturum(16) seq(4) total(4) payload_uz(4) crc32(4)
HEADER = struct.Struct("!4sBBH16sIIHI")
MAX_PAYLOAD_SIZE = 60_000


class ProtocolError(ValueError):
    """Datagram geçerli bir NetProbe paketi değilse fırlatılır."""


class PacketType(enum.IntEnum):
    START = 1
    DATA = 2
    ACK = 3
    END = 4
    RESULT = 5
    ERROR = 6


@dataclass(frozen=True)
class Packet:
    packet_type: PacketType
    session_id: str
    sequence: int
    total_packets: int
    payload: bytes
    flags: int = 0
    checksum: int = 0


def new_session_id() -> str:
    return uuid.uuid4().hex


def _session_to_bytes(session_id: str | uuid.UUID) -> bytes:
    if isinstance(session_id, uuid.UUID):
        return session_id.bytes
    try:
        return uuid.UUID(hex=session_id.replace("-", "")).bytes
    except ValueError as exc:
        raise ProtocolError(f"invalid session id: {session_id}") from exc


def _session_from_bytes(raw: bytes) -> str:
    return uuid.UUID(bytes=raw).hex


def payload_checksum(payload: bytes) -> int:
    return zlib.crc32(payload) & 0xFFFFFFFF


def encode_packet(
    packet_type: PacketType,
    session_id: str,
    sequence: int = 0,
    total_packets: int = 0,
    payload: bytes = b"",
    flags: int = 0,
) -> bytes:
    if len(payload) > MAX_PAYLOAD_SIZE:
        raise ProtocolError(f"payload too large: {len(payload)} bytes")
    if sequence < 0 or total_packets < 0:
        raise ProtocolError("sequence and total_packets must not be negative")

    checksum = payload_checksum(payload)
    header = HEADER.pack(
        MAGIC,
        VERSION,
        int(packet_type),
        flags,
        _session_to_bytes(session_id),
        sequence,
        total_packets,
        len(payload),
        checksum,
    )
    return header + payload


def decode_packet(datagram: bytes) -> Packet:
    if len(datagram) < HEADER.size:
        raise ProtocolError("datagram is shorter than the NetProbe header")
    magic, version, packet_type, flags, session_raw, sequence, total_packets, payload_len, checksum = HEADER.unpack(
        datagram[: HEADER.size]
    )
    if magic != MAGIC:
        raise ProtocolError("invalid packet magic")
    if version != VERSION:
        raise ProtocolError(f"unsupported protocol version: {version}")
    try:
        parsed_type = PacketType(packet_type)
    except ValueError as exc:
        raise ProtocolError(f"unknown packet type: {packet_type}") from exc

    payload = datagram[HEADER.size :]
    if len(payload) != payload_len:
        raise ProtocolError("payload length does not match header")
    if payload_checksum(payload) != checksum:
        raise ProtocolError("payload checksum mismatch")

    return Packet(
        packet_type=parsed_type,
        session_id=_session_from_bytes(session_raw),
        sequence=sequence,
        total_packets=total_packets,
        payload=payload,
        flags=flags,
        checksum=checksum,
    )


def encode_json_packet(
    packet_type: PacketType,
    session_id: str,
    payload: dict[str, Any],
    sequence: int = 0,
    total_packets: int = 0,
    flags: int = 0,
) -> bytes:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return encode_packet(packet_type, session_id, sequence, total_packets, raw, flags)


def decode_json_payload(packet: Packet) -> dict[str, Any]:
    try:
        value = json.loads(packet.payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("packet payload is not valid JSON") from exc
    if not isinstance(value, dict):
        raise ProtocolError("packet JSON payload must be an object")
    return value


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def split_file(path: str | Path, payload_size: int) -> list[bytes]:
    if payload_size <= 0:
        raise ValueError("payload_size must be positive")
    chunks: list[bytes] = []
    with Path(path).open("rb") as handle:
        while True:
            chunk = handle.read(payload_size)
            if not chunk:
                break
            chunks.append(chunk)
    return chunks


def safe_filename(name: str) -> str:
    cleaned = Path(name).name.strip() or "received.bin"
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", cleaned)
    return cleaned[:180] or "received.bin"
