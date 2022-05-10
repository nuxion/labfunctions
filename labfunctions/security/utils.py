import binascii
import importlib
import os
from datetime import datetime, timedelta

from labfunctions.types.security import KeyPairs


def open_keys(pub, priv) -> KeyPairs:
    with open(pub, "r") as f:
        pub = f.read()
        pub = pub.strip()
    with open(priv, "r") as f:
        priv = f.read()
        priv = priv.strip()
    return KeyPairs(public=pub, private=priv)


def generate_token(n=24, *args, **kwargs):
    return str(binascii.hexlify(os.urandom(n)), "utf-8")


def get_delta(delta_min: int) -> int:
    """Returns a timestamp addding a delta_min value to the utc now date."""
    delta = datetime.utcnow() + timedelta(minutes=delta_min)
    return int(delta.timestamp())
