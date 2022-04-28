from typing import Union

from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


class PasswordScript:
    """
    https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/#cryptography.hazmat.primitives.kdf.scrypt.Scrypt
    """

    def __init__(self, salt: Union[bytes, str], n=2**14, r=8, p=1):
        if isinstance(salt, str):
            salt = salt.encode("utf-8")
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

    def verify(self, unencypted: str, encrypted: bytes) -> bool:
        """Verify if a uncrypted text match with an encrypted one"""
        kdf = self._kdf()
        try:
            kdf.verify(unencypted.encode("utf-8"), encrypted)
            return True
        except:
            return False
