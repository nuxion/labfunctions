import binascii
import importlib
import os

from nb_workflows.types.security import KeyPairs


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
