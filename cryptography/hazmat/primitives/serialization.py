# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import, division, print_function

import base64
import binascii
import io
import re
import warnings

from pyasn1.codec.der import decoder
from pyasn1.type import namedtype, namedval, tag, univ

from cryptography import utils
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def load_pem_traditional_openssl_private_key(data, password, backend):
    warnings.warn(
        "load_pem_traditional_openssl_private_key is deprecated and will be "
        "removed in a future version, use load_pem_private_key instead.",
        utils.DeprecatedIn06,
        stacklevel=2
    )

    return backend.load_traditional_openssl_pem_private_key(
        data, password
    )


def load_pem_pkcs8_private_key(data, password, backend):
    warnings.warn(
        "load_pem_pkcs8_private_key is deprecated and will be removed in a "
        "future version, use load_pem_private_key instead.",
        utils.DeprecatedIn06,
        stacklevel=2
    )

    return backend.load_pkcs8_pem_private_key(data, password)


def load_pem_private_key(data, password, backend):
    pem = _PEMObject.find_pem(data)
    pem = pem.handle_encrypted(password, backend)
    parser_type = _PRIVATE_KEY_PARSERS[pem._object_type]
    return parser_type(backend).load_object(pem)


def load_pem_public_key(data, backend):
    return backend.load_pem_public_key(data)


class _OtherPrimeInfo(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedTypes("prime", univ.Integer()),
        namedtype.NamedTypes("exponent", univ.Integer()),
        namedtype.NamedTypes("coefficient", univ.Integer()),
    )


class _OtherPrimeInfos(univ.SequenceOf):
    componentType = _OtherPrimeInfo()


class _RSAPrivateKey(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType(
            "version",
            univ.Integer(
                namedValues=namedval.NamedValues(
                    ("two-prime", 0),
                    ("multi", 1),
                )
            )
        ),
        namedtype.NamedType("modulus", univ.Integer()),
        namedtype.NamedType("publicExponent", univ.Integer()),
        namedtype.NamedType("privateExponent", univ.Integer()),
        namedtype.NamedType("prime1", univ.Integer()),
        namedtype.NamedType("prime2", univ.Integer()),
        namedtype.NamedType("exponent1", univ.Integer()),
        namedtype.NamedType("exponent2", univ.Integer()),
        namedtype.NamedType("coefficient", univ.Integer()),
        namedtype.OptionalNamedType("otherPrimeInfos", _OtherPrimeInfos())
    )


class _RSAPrivateKeyParser(object):
    def __init__(self, backend):
        self._backend = backend

    def load_object(self, pem):
        asn1_private_key, _ = decoder.decode(
            pem._body, asn1Spec=_RSAPrivateKey()
        )
        assert asn1_private_key.getComponentByName("version") == 0
        return rsa.RSAPrivateNumbers(
            int(asn1_private_key.getComponentByName("prime1")),
            int(asn1_private_key.getComponentByName("prime2")),
            int(asn1_private_key.getComponentByName("privateExponent")),
            int(asn1_private_key.getComponentByName("exponent1")),
            int(asn1_private_key.getComponentByName("exponent2")),
            int(asn1_private_key.getComponentByName("coefficient")),
            rsa.RSAPublicNumbers(
                int(asn1_private_key.getComponentByName("publicExponent")),
                int(asn1_private_key.getComponentByName("modulus")),
            )
        ).private_key(self._backend)


class _ECParameters(univ.Choice):
    # TODO: There are a few more options for this choice I think, the RFC says
    # not to use them though...
    componentType = namedtype.NamedTypes(
        namedtype.NamedType("namedCurve", univ.ObjectIdentifier()),
    )


class _ECPrivateKey(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType(
            "version",
            univ.Integer(
                namedValues=namedval.NamedValues(
                    ("ecPrivkeyVer1", 1),
                )
            ),
        ),
        namedtype.NamedType("privateKey", univ.OctetString()),
        namedtype.OptionalNamedType("parameters", _ECParameters().subtype(
            implicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatSimple, 0),
        )),
        namedtype.OptionalNamedType("publicKey", univ.BitString().subtype(
            implicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatSimple, 1),
        )),
    )


def bytes_to_int(b):
    return sum(c << (i * 8) for i, c in enumerate(reversed(b)))


def bits_to_int(b):
    return sum(c << i for i, c in enumerate(b))


def bits_to_bytes(b):
    return [
        bits_to_int(reversed(b[i:i + 8]))
        for i in xrange(0, len(b), 8)
    ]


class _ECDSAPrivateKeyParser(object):
    def __init__(self, backend):
        self._backend = backend

    def load_object(self, pem):
        asn1_private_key, _ = decoder.decode(
            pem._body, asn1Spec=_ECPrivateKey()
        )

        private_value = bytes_to_int(
            map(ord, asn1_private_key.getComponentByName("privateKey"))
        )
        public_key = bits_to_bytes(
            asn1_private_key.getComponentByName("publicKey")
        )
        if public_key[0] != 4:
            raise ValueError

        curve_oid = asn1_private_key.getComponentByName(
            "parameters"
        ).getComponent(0).asTuple()
        curve = ec._OID_TO_CURVE[curve_oid]()

        x = bytes_to_int(public_key[1:(curve.key_size // 8) + 1])
        y = bytes_to_int(public_key[(curve.key_size // 8) + 1:])

        return ec.EllipticCurvePrivateNumbers(
            private_value,
            ec.EllipticCurvePublicNumbers(
                x, y, curve
            )
        ).private_key(self._backend)


_PRIVATE_KEY_PARSERS = {
    "EC PRIVATE KEY": _ECDSAPrivateKeyParser,
    "RSA PRIVATE KEY": _RSAPrivateKeyParser,
}


_PEM_BEGIN_RE = re.compile(b"-----BEGIN ([\w ]+?)-----")


class _PEMCipher(object):
    def __init__(self, algorithm_cls, mode_cls, key_size):
        self._algorithm_cls = algorithm_cls
        self._mode_cls = mode_cls
        self._key_size = key_size

    def _derive_key(self, password, salt, backend):
        key = b""
        while len(key) < self._key_size:
            hasher = hashes.Hash(hashes.MD5(), backend=backend)
            hasher.update(key)
            hasher.update(password)
            hasher.update(salt)
            key += hasher.finalize()
        return key[:self._key_size]

    def decrypt(self, data, password, iv, backend):
        key = self._derive_key(password, iv[:8], backend)
        decryptor = Cipher(
            self._algorithm_cls(key),
            self._mode_cls(iv),
            backend=backend
        ).decryptor()
        decrypted_data = decryptor.update(data) + decryptor.finalize()
        unpadder = padding.PKCS7(self._algorithm_cls.block_size).unpadder()
        return unpadder.update(decrypted_data) + unpadder.finalize()


_PEM_CIPHERS = {
    "AES-256-CBC": _PEMCipher(algorithms.AES, modes.CBC, 256 // 8),
    "DES-EDE3-CBC": _PEMCipher(algorithms.TripleDES, modes.CBC, 192 // 8),
}


class _PEMObject(object):
    def __init__(self, object_type, headers, body):
        self._object_type = object_type
        self._headers = headers
        self._body = body

    @classmethod
    def find_pem(cls, data):
        data = io.BytesIO(data)
        for line in data:
            match = _PEM_BEGIN_RE.match(line)
            if match is not None:
                break
        else:
            raise ValueError("no PEM object")

        object_type = match.group(1)
        body_lines = []
        headers = []
        for line in data:
            line = line.strip()
            if b":" in line:
                # TODO: line continuations :-()
                name, value = line.split(b":", 1)
                headers.append((name, value.strip()))
            elif line == b"-----END {0}-----".format(object_type):
                break
            else:
                body_lines.append(line)
        else:
            raise ValueError("No end marker")

        return cls(
            object_type, headers, base64.b64decode(b"".join(body_lines))
        )

    def handle_encrypted(self, password, backend):
        encrypted = False
        dek_info = None
        for key, value in self._headers:
            if key == "Proc-Type" and value == "4,ENCRYPTED":
                encrypted = True
            elif key == "DEK-Info":
                dek_info = value

        if not encrypted:
            return self
        elif dek_info is None:
            raise ValueError("Missing DEK-INFO")

        algorithm_name, hex_iv = dek_info.split(",", 1)
        iv = binascii.unhexlify(hex_iv)
        pem_cipher = _PEM_CIPHERS[algorithm_name]
        body = pem_cipher.decrypt(self._body, password, iv, backend)
        return _PEMObject(self._object_type, [], body)
