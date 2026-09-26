"""Herdr v1.1 durable TaskGraph contract.

Canonical implementation for Bbambaaamm/herdr#2, migrated and hardened from
the former Autonomous-Quant-Lab#230 prototype.

The module is consumer-agnostic. Consumer safety rules (for example QuantLab
PAPER-only) remain in the consumer policy layer and are never generalized here.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

GRAPH_VERSION = "1.1.0"
HARD_MAX_NODES = 256
HARD_MAX_DEPTH = 16
HARD_MAX_FANOUT = 16
HARD_MAX_TIMEOUT_SECONDS = 86_400
HARD_MAX_ATTEMPTS = 10

DEFAULT_MAX_NODES = HARD_MAX_NODES
DEFAULT_MAX_DEPTH = HARD_MAX_DEPTH
DEFAULT_MAX_FANOUT = HARD_MAX_FANOUT
DEFAULT_TIMEOUT_SECONDS = 1_800
DEFAULT_MAX_ATTEMPTS = 1

_SECRET_KEY_FRAGMENTS = (
    "secret", "token", "password", "passwd", "apikey", "api_key", "api-key",
    "access_key", "accesskey", "credential", "private_key", "privatekey",
)
_SECRET_VALUE_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
)


class GraphValidationError(ValueError):
    """TaskGraph input violated the fail-closed contract."""


class LifecycleState(StrEnum):
