from __future__ import annotations

from netprobe.events import EventLogger, latest_event_files, read_recent_events


def test_recent_events_reads_nested_log_directories(tmp_path) -> None:
    client = EventLogger(tmp_path / "web_client", "client_demo", "client")
    server = EventLogger(tmp_path / "web_server", "server", "server")

    client.log("packet_sent", sequence=1)
    server.log("ack_sent", sequence=1)

    files = latest_event_files(tmp_path)
    assert client.path in files
    assert server.path in files

    events = read_recent_events(tmp_path)
    assert [event["event"] for event in events] == ["packet_sent", "ack_sent"]
