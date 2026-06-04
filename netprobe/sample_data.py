from __future__ import annotations

import random
from pathlib import Path

from .config import SAMPLE_DIR


SAMPLES = {
    "small_16kb.bin": 16 * 1024,
    "medium_128kb.bin": 128 * 1024,
    "large_512kb.bin": 512 * 1024,
}


def ensure_sample_files(sample_dir: str | Path = SAMPLE_DIR) -> list[Path]:
    root = Path(sample_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for index, (name, size) in enumerate(SAMPLES.items()):
        path = root / name
        if not path.exists() or path.stat().st_size != size:
            rng = random.Random(10_000 + index)
            with path.open("wb") as handle:
                remaining = size
                while remaining > 0:
                    block_size = min(4096, remaining)
                    handle.write(bytes(rng.randrange(0, 256) for _ in range(block_size)))
                    remaining -= block_size
        paths.append(path)
    return paths


def main() -> None:
    for path in ensure_sample_files():
        print(f"{path} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
