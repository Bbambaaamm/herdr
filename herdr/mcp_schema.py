"""Disposable, offline JSON Schema 2020-12 validator for the MCP boundary."""
import json
import sys


def main():
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
        resource.setrlimit(resource.RLIMIT_AS, (256_000_000, 256_000_000))
        from jsonschema import Draft202012Validator
        from referencing import Registry
    except ImportError:
        return 78
    try:
        raw = sys.stdin.buffer.read(2_000_001)
        if len(raw) > 2_000_000:
            return 1
        data = json.loads(raw)
        schema = data["schema"]
        if not isinstance(schema, dict) or schema.get("$schema", "https://json-schema.org/draft/2020-12/schema") != "https://json-schema.org/draft/2020-12/schema":
            return 1
        nodes = 0
        def walk(value, depth=0):
            nonlocal nodes
            nodes += 1
            if nodes > 1024 or depth > 16:
                raise ValueError("schema bounds")
            if isinstance(value, dict):
                for key, item in value.items():
                    if key in {"$ref", "$dynamicRef"} and (not isinstance(item, str) or not item.startswith("#")):
                        raise ValueError("external reference denied")
                    if key in {"pattern", "patternProperties"}:
                        # Full regex semantics are supported in the bounded process.
                        if len(json.dumps(item)) > 4096:
                            raise ValueError("regex bounds")
                    walk(item, depth + 1)
            elif isinstance(value, list):
                for item in value:
                    walk(item, depth + 1)
        walk(schema)
        Draft202012Validator.check_schema(schema)
        def denied(uri):
            raise ValueError("external reference denied")
        validator = Draft202012Validator(schema, registry=Registry(retrieve=denied))
        if not data["check_only"] and not validator.is_valid(data["instance"]):
            return 1
        sys.stdout.buffer.write(b"valid")
        return 0
    except Exception:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
