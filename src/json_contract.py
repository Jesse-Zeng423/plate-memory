"""Strict JSON decoding for local profiles and untrusted structured outputs."""
import json


class JsonContractError(ValueError):
    pass


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise JsonContractError(f"Duplicate JSON field: {key}")
        result[key] = value
    return result


def _constant(value):
    raise JsonContractError(f"Non-JSON numeric constant: {value}")


def loads(raw):
    return json.loads(raw, object_pairs_hook=_object, parse_constant=_constant)
