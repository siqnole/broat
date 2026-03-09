#!/usr/bin/env python3
"""Entry point for the Bronx Stoat.chat bot."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Load .env file if it exists (no extra dependency needed)
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

from bot.core import Bronx


def main() -> None:
    bot = Bronx()
    bot.run(token=os.environ["BOT_TOKEN"], bot=True)


if __name__ == "__main__":
    main()
