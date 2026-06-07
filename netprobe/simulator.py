"""İstemci tarafı ağ bozulması: olasılıksal kayıp ve isteğe bağlı gecikme/sapma."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass


@dataclass
class NetworkSimulator:
    loss_rate: float = 0.0
    delay_ms: float = 0.0
    jitter_ms: float = 0.0
    seed: int | None = 42

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def should_drop(self) -> bool:
        return self.loss_rate > 0 and self._rng.random() < self.loss_rate

    def apply_delay(self) -> None:
        delay = self.delay_ms
        if self.jitter_ms:
            delay += self._rng.uniform(-self.jitter_ms, self.jitter_ms)
        if delay > 0:
            time.sleep(delay / 1000)
