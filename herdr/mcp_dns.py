"""Disposable credential-free resolver; the caller kills it at its deadline."""
import json
import socket
import sys

def main():
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (128_000_000, 128_000_000))
        resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
        raw = sys.stdin.buffer.read(4097)
        if len(raw) > 4096:
            return 1
        value = json.loads(raw)
        if (set(value) != {"hostname","port"} or not isinstance(value["hostname"],str)
                or not 0 < len(value["hostname"]) <= 255
                or type(value["port"]) is not int or not 1 <= value["port"] <= 65535):
            return 1
        rows = socket.getaddrinfo(value["hostname"],value["port"],type=socket.SOCK_STREAM)
        addresses, seen = [], set()
        for family, kind, protocol, _, address in rows:
            if family not in (socket.AF_INET,socket.AF_INET6) or kind != socket.SOCK_STREAM:
                continue
            item = (family, protocol, tuple(address))
            if item not in seen:
                seen.add(item)
                addresses.append(item)
            if len(addresses) >= 16:
                break
        payload = json.dumps(addresses,separators=(",",":")).encode()
        if not addresses or len(payload) > 8192:
            return 1
        sys.stdout.buffer.write(payload)
        return 0
    except Exception:
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
