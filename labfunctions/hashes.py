import binascii
import os
import time
from dataclasses import dataclass

from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from nanoid import generate

from labfunctions.defaults import NANO_ID_ALPHABET


def generate_random(size=10, strategy="nanoid", alphabet=NANO_ID_ALPHABET) -> str:
    """Default URLSafe id"""
    if strategy == "nanoid":
        return generate(alphabet=alphabet, size=size)
    raise NotImplementedError("Strategy %s not implemented", strategy)


@dataclass
class Hash96:
    """A custom id generator of 96 bits long, compose as:
        [ 41 bits -> TS ][55 bits of a random number]
    in this way the generated ids are naturally ordered by time.
    """

    id_int: int
    id_hex: str

    @classmethod
    def time_random_string(cls):
        """
        It generates a random string based on a time epoch
        an a random number.
        It's a 96 bit long

        """
        # 41 bits timestamp with a custom epoch
        ts = int(time.time())
        # 55 bits a random number
        num = int.from_bytes(os.urandom(90), "big") % 2**55
        _int_id = (ts << 55) | (num << 0)
        _bytes = _int_id.to_bytes(12, "big")
        _bytes_id = binascii.hexlify(_bytes).decode()

        return cls(id_int=_int_id, id_hex=_bytes_id)


class PasswordScript:
    """
    https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/#cryptography.hazmat.primitives.kdf.scrypt.Scrypt
    """

    def __init__(self, salt: bytes, n=2**14, r=8, p=1):
        self.n = n
        self.r = r
        self.p = p
        self.salt = salt

    def _kdf(self):
        kdf = Scrypt(
            salt=self.salt,
            length=32,
            n=self.n,
            r=self.r,
            p=self.p,
        )
        return kdf

    def encrypt(self, pass_: str) -> bytes:
        kdf = self._kdf()

        return kdf.derive(pass_.encode("utf-8"))

    def verify(self, pass_: str, key: bytes) -> bool:
        kdf = self._kdf()
        try:
            kdf.verify(pass_.encode("utf-8"), key)
            return True
        except:
            return False
