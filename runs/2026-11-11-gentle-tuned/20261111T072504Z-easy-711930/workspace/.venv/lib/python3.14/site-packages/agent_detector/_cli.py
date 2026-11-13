from __future__ import annotations

import argparse
from collections.abc import Sequence
from typing import cast

from agent_detector import AgentConfidence, detect_agent


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agent-detector",
        description="Detect which AI coding agent is driving the current process.",
    )
    parser.add_argument(
        "--minimum-confidence",
        choices=("high", "medium", "low"),
        default="low",
        help="Ignore detections weaker than this (default: low).",
    )
    args = parser.parse_args(argv)

    detection = detect_agent(
        minimum_confidence=cast(AgentConfidence, args.minimum_confidence),
    )
    if detection is None:
        print("unattributed")
        return 1

    print(detection)
    return 0
