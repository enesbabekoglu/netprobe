from __future__ import annotations

import pytest

from netprobe.protocol import PacketType, ProtocolError, decode_packet, encode_packet, new_session_id


def test_packet_roundtrip_preserves_fields() -> None:
    session_id = new_session_id()
    raw = encode_packet(PacketType.DATA, session_id, sequence=7, total_packets=9, payload=b"hello")
    packet = decode_packet(raw)
    assert packet.packet_type == PacketType.DATA
    assert packet.session_id == session_id
    assert packet.sequence == 7
    assert packet.total_packets == 9
    assert packet.payload == b"hello"


def test_checksum_mismatch_is_rejected() -> None:
    session_id = new_session_id()
    raw = bytearray(encode_packet(PacketType.DATA, session_id, payload=b"abc"))
    raw[-1] ^= 0xFF
    with pytest.raises(ProtocolError, match="checksum"):
        decode_packet(bytes(raw))
