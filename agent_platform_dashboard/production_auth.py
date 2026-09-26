"""Bounded Basic verification from an explicit admin-created PBKDF2 record."""
import base64
import hashlib
import hmac

from . import production_contract as c

ITERATIONS = 600000


def verifier(value):
    c.keys(value, 'version username salt verifier profiles')
    c.need(type(value['version']) is int and value['version'] == 1 and value['username'] == 'michal')
    c.need(c.hex_id(value['salt'], (32,)) and c.hex_id(value['verifier']))
    c.need(type(value['profiles']) is list and 1 <= len(value['profiles']) <= 2
           and all(type(p) is str and p in c.PROFILES for p in value['profiles'])
           and len(set(value['profiles'])) == len(value['profiles']))
    return value


def authenticate(header, record):
    if type(header) is not str or not header.startswith('Basic ') or len(header) > 512:
        return False
    try:
        data = base64.b64decode(header[6:], validate=True)
        username, password = data.split(b':', 1)
        if username != b'michal' or not 24 <= len(password) <= 128:
            return False
        actual = hashlib.pbkdf2_hmac('sha256', password, bytes.fromhex(record['salt']), ITERATIONS).hex()
        return hmac.compare_digest(actual, record['verifier'])
    except (ValueError, TypeError):
        return False
