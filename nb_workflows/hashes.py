import binascii
import os
import time
from dataclasses import dataclass


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
