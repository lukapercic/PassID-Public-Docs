import base64
from datetime import datetime
from math import log
from typing import cast, Union
import os

from cryptography.hazmat.primitives.hashes import Hash, SHA512_256
from cryptography.hazmat.backends import default_backend



class CID(int):
    """ Represents challenge id """

    def __new__(cls, cid: Union[int, bytes, str], *args, **kwargs) -> "CID":
        if isinstance(cid, int):
            if not (-0xFFFFFFFF <= cid <= 0xFFFFFFFF):
                raise ValueError("cid integer too big")
        elif isinstance(cid, bytes):
            if len(cid) < 4:
                raise ValueError("cid bytes too small")
            cid = int.from_bytes(cid[0:4], 'big')
        elif isinstance(cid, str):
            cid = int(cid)
            if not (-0xFFFFFFFF <= cid <= 0xFFFFFFFF):
                raise ValueError("cid integer string too big")
        else:
            raise ValueError("invalid cid type")
        return cast(CID, super().__new__(cls, cid))  # type: ignore  # https://github.com/python/typeshed/issues/2630  # noqa: E501

    def hex(self):
        return hex(self)

    @classmethod
    def fromhex(cls, hexCid: str) -> "CID":
        assert isinstance(hexCid, str)
        return cls(int(hexCid, 16))


class ChallengeError(Exception):
    pass

class Challenge(bytes):
    """ Class generates and holds proto challenge """

    _hash_algo = SHA512_256

    def __new__(cls, challenge: bytes) -> "Challenge":
        if isinstance(challenge, bytes):
            if len(challenge) != cls._hash_algo.digest_size:
                raise ChallengeError("Invalid challenge length")
            return cast(Challenge, super().__new__(cls, challenge))  # type: ignore  # https://github.com/python/typeshed/issues/2630  # noqa: E501
        else:
            raise ChallengeError("Invalid challenge type")

    @property
    def id(self) -> CID:
        if not hasattr(self, "_id"):
            self._id = CID(self)
        return self._id

    @staticmethod
    def fromhex(hexStr: str) -> "Challenge":
        assert isinstance(hexStr, str)
        return Challenge(bytes.fromhex(hexStr))

    @staticmethod
    def fromBase64(b64Str: str) -> "Challenge":
        assert isinstance(b64Str, str)
        return Challenge(base64.b64decode(b64Str))

    def toBase64(self):
        return str(base64.b64encode(self), 'ascii')

    @staticmethod
    def generate(time: datetime) -> "Challenge":
        assert isinstance(time, datetime)
        ts = int(time.timestamp())
        ts = ts.to_bytes((ts.bit_length() + 7) // 8, 'big')
        rs = os.urandom(Challenge._hash_algo.digest_size)

        h = Hash(Challenge._hash_algo(), backend=default_backend())
        h.update(ts)
        h.update(rs)

        return Challenge(h.finalize())