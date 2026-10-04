"""Disposable, offline JSON Schema 2020-12 validator for the MCP boundary."""
import json
import sys


def main():
    try:
        import resource
        for kind, ceiling in ((resource.RLIMIT_CPU, 2), (resource.RLIMIT_AS, 256_000_000)):
            _, hard = resource.getrlimit(kind)
            soft = ceiling if hard == resource.RLIM_INFINITY else min(ceiling, hard)
            resource.setrlimit(kind, (soft, hard))
        from jsonschema import Draft202012Validator
        from jsonschema.exceptions import SchemaError, ValidationError
        from referencing import Registry
        from referencing.exceptions import Unresolvable
    except (ImportError, ValueError, OSError, MemoryError):
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
        def bounded(value, depth=0):
            nonlocal nodes
            nodes += 1
            if nodes > 1024 or depth > 16:
                raise ValueError("schema bounds")
            if isinstance(value, dict):
                for item in value.values():
                    bounded(item, depth + 1)
            elif isinstance(value, list):
                for item in value:
                    bounded(item, depth + 1)
        bounded(schema)

        # Only recognized subschema locations carry schema keywords.
        # Property names and const/default/example payloads are ordinary data.
        single = {"additionalProperties", "unevaluatedProperties", "propertyNames",
                  "contentSchema", "items", "contains", "unevaluatedItems", "not",
                  "if", "then", "else"}
        mappings = {"$defs", "definitions", "properties", "patternProperties", "dependentSchemas"}
        arrays = {"allOf", "anyOf", "oneOf", "prefixItems"}
        def inspect(value):
            if not isinstance(value, dict):
                return
            for key in ("$ref", "$dynamicRef"):
                if key in value and (not isinstance(value[key], str) or not value[key].startswith("#")):
                    raise ValueError("external reference denied")
            for key in ("pattern", "patternProperties"):
                if key in value and len(json.dumps(value[key])) > 4096:
                    raise ValueError("regex bounds")
            for key, item in value.items():
                if key in single:
                    inspect(item)
                elif key in mappings and isinstance(item, dict):
                    for child in item.values():
                        inspect(child)
                elif key in arrays and isinstance(item, list):
                    for child in item:
                        inspect(child)
        inspect(schema)
        Draft202012Validator.check_schema(schema)
        def denied(uri):
            raise ValueError("external reference denied")
        validator = Draft202012Validator(schema, registry=Registry(retrieve=denied))
        if not data["check_only"] and not validator.is_valid(data["instance"]):
            return 1
        sys.stdout.buffer.write(b"valid")
        return 0
    except (SchemaError, ValidationError, Unresolvable, ValueError, KeyError, TypeError):
        return 1
    except Exception:
        # Resource exhaustion and helper faults do not invalidate the caller's schema.
        return 78


if __name__ == "__main__":
    raise SystemExit(main())
