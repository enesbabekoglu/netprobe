from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_HOST = "127.0.0.1"
DEFAULT_UDP_PORT = 9999
DEFAULT_TCP_PORT = 10099
DEFAULT_PAYLOAD_SIZE = 1024
DEFAULT_TIMEOUT = 0.5
DEFAULT_MAX_RETRIES = 5
DEFAULT_WINDOW_SIZE = 8

DATA_DIR = PROJECT_ROOT / "data"
SAMPLE_DIR = DATA_DIR / "sample_files"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
LOG_DIR = PROJECT_ROOT / "logs"
RECEIVED_DIR = PROJECT_ROOT / "received"


@dataclass(frozen=True)
class TransferConfig:
    host: str = DEFAULT_HOST
    port: int = DEFAULT_UDP_PORT
    payload_size: int = DEFAULT_PAYLOAD_SIZE
    timeout: float = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES
    window_size: int = DEFAULT_WINDOW_SIZE
    loss_rate: float = 0.0
    delay_ms: float = 0.0
    jitter_ms: float = 0.0
    seed: int | None = 42
    log_dir: Path = LOG_DIR

    def validate(self) -> None:
        if self.payload_size <= 0 or self.payload_size > 60_000:
            raise ValueError("payload_size must be between 1 and 60000 bytes")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries must not be negative")
        if self.window_size <= 0:
            raise ValueError("window_size must be positive")
        if not 0.0 <= self.loss_rate <= 1.0:
            raise ValueError("loss_rate must be between 0.0 and 1.0")
        if self.delay_ms < 0 or self.jitter_ms < 0:
            raise ValueError("delay_ms and jitter_ms must not be negative")
