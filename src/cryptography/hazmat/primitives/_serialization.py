# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.

import abc
import typing

from cryptography import utils

# This exists to break an import cycle. These classes are normally accessible
# from the serialization module.


class Encoding(utils.Enum):
    PEM = "PEM"
    DER = "DER"
    OpenSSH = "OpenSSH"
    Raw = "Raw"
    X962 = "ANSI X9.62"
    SMIME = "S/MIME"


class PrivateFormat(utils.Enum):
    PKCS8 = "PKCS8"
    TraditionalOpenSSL = "TraditionalOpenSSL"
    Raw = "Raw"
    OpenSSH = "OpenSSH"


class PublicFormat(utils.Enum):
    SubjectPublicKeyInfo = "X.509 subjectPublicKeyInfo with PKCS#1"
    PKCS1 = "Raw PKCS#1"
    OpenSSH = "OpenSSH"
    Raw = "Raw"
    CompressedPoint = "X9.62 Compressed Point"
    UncompressedPoint = "X9.62 Uncompressed Point"


class ParameterFormat(utils.Enum):
    PKCS3 = "PKCS3"


class KeySerializationEncryption(metaclass=abc.ABCMeta):
    pass


class BestAvailableEncryption(KeySerializationEncryption):
    def __init__(
        self, password: bytes, kdf_rounds: typing.Optional[int] = None
    ):
        if not isinstance(password, bytes) or len(password) == 0:
            raise ValueError("Password must be 1 or more bytes.")

        if kdf_rounds is not None and not isinstance(kdf_rounds, int):
            raise ValueError("KDF rounds must be of type 'int'")

        self.password = password
        self.kdf_rounds = kdf_rounds


class NoEncryption(KeySerializationEncryption):
    pass
