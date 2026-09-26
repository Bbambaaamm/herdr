#!/usr/bin/env python3
"""Replace insecure RNG calls in the checked-in browser bundle."""
from pathlib import Path
import sys

MARKER = "const __agentPlatformSecureRandom="
PREFIX = """const __agentPlatformSecureRandom=(()=>{const words=new Uint32Array(256);let index=words.length;return()=>{const crypto=globalThis.crypto;if(!crypto||typeof crypto.getRandomValues!==\"function\")throw new Error(\"secure_random_unavailable\");if(index>=words.length){crypto.getRandomValues(words);index=0}return words[index++]/4294967296}})();
"""

def harden(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    if text.startswith(MARKER):
        if "Math.random" in text:
            raise SystemExit("hardened bundle still contains Math.random")
        return 0
    count = text.count("Math.random")
    if count == 0:
        raise SystemExit("expected Math.random calls in input bundle")
    hardened = PREFIX + text.replace("Math.random", "__agentPlatformSecureRandom")
    path.write_text(hardened, encoding="utf-8")
    return count

def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: harden-machine-city-random.py BUNDLE")
    count = harden(Path(sys.argv[1]))
    print(f"hardened_random_calls={count}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
