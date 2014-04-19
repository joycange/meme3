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

import six

from cryptography import utils
from cryptography.hazmat.primitives import interfaces


@utils.register_interface(interfaces.EllipticCurve)
class sect571r1(object):
    @property
    def name(self):
        return "sect571r1"

    @property
    def key_size(self):
        return 571


@utils.register_interface(interfaces.EllipticCurve)
class sect409r1(object):
    @property
    def name(self):
        return "sect409r1"

    @property
    def key_size(self):
        return 409


@utils.register_interface(interfaces.EllipticCurve)
class sect283r1(object):
    @property
    def name(self):
        return "sect283r1"

    @property
    def key_size(self):
        return 283


@utils.register_interface(interfaces.EllipticCurve)
class sect233r1(object):
    @property
    def name(self):
        return "sect233r1"

    @property
    def key_size(self):
        return 233


@utils.register_interface(interfaces.EllipticCurve)
class sect163r2(object):
    @property
    def name(self):
        return "sect163r2"

    @property
    def key_size(self):
        return 163


@utils.register_interface(interfaces.EllipticCurve)
class sect571k1(object):
    @property
    def name(self):
        return "sect571k1"

    @property
    def key_size(self):
        return 571


@utils.register_interface(interfaces.EllipticCurve)
class sect409k1(object):
    @property
    def name(self):
        return "sect409k1"

    @property
    def key_size(self):
        return 409


@utils.register_interface(interfaces.EllipticCurve)
class sect283k1(object):
    @property
    def name(self):
        return "sect283k1"

    @property
    def key_size(self):
        return 283


@utils.register_interface(interfaces.EllipticCurve)
class sect233k1(object):
    @property
    def name(self):
        return "sect233k1"

    @property
    def key_size(self):
        return 233


@utils.register_interface(interfaces.EllipticCurve)
class sect163k1(object):
    @property
    def name(self):
        return "sect163k1"

    @property
    def key_size(self):
        return 163


@utils.register_interface(interfaces.EllipticCurve)
class secp521r1(object):
    @property
    def name(self):
        return "secp521r1"

    @property
    def key_size(self):
        return 521


@utils.register_interface(interfaces.EllipticCurve)
class secp384r1(object):
    @property
    def name(self):
        return "secp384r1"

    @property
    def key_size(self):
        return 384


@utils.register_interface(interfaces.EllipticCurve)
class secp256r1(object):
    @property
    def name(self):
        return "secp256r1"

    @property
    def key_size(self):
        return 256


@utils.register_interface(interfaces.EllipticCurve)
class secp224r1(object):
    @property
    def name(self):
        return "secp224r1"

    @property
    def key_size(self):
        return 224


@utils.register_interface(interfaces.EllipticCurve)
class secp192r1(object):
    @property
    def name(self):
        return "secp192r1"

    @property
    def key_size(self):
        return 192


@utils.register_interface(interfaces.EllipticCurveSignatureAlgorithm)
class ECDSA(object):
    def __init__(self, algorithm):
        self._algorithm = algorithm

    @property
    def algorithm(self):
        return self._algorithm

    def signer(self, private_key, backend):
        return backend.create_ecdsa_signature_ctx(
            private_key, self.algorithm)

    def verifier(self, signature, public_key, backend):
        return backend.create_ecdsa_verification_ctx(
            public_key, signature, self.algorithm)


@utils.register_interface(interfaces.EllipticCurvePublicKey)
class EllipticCurvePublicKey(object):
    def __init__(self, x, y, curve):
        if (
            not isinstance(x, six.integer_types) or
            not isinstance(y, six.integer_types)
        ):
            raise TypeError("private_key, x and y must be integers.")

        if not isinstance(curve, interfaces.EllipticCurve):
            raise TypeError("curve must provide the EllipticCurve interface.")

        self._y = y
        self._x = x
        self._curve = curve

    def verifier(self, signature, signature_algorithm, backend):
        return signature_algorithm.verifier(signature, self, backend)

    @property
    def key_size(self):
        return self._curve.key_size

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def curve(self):
        return self._curve


@utils.register_interface(interfaces.EllipticCurvePrivateKey)
class EllipticCurvePrivateKey(object):
    def __init__(self, private_key, x, y, curve):
        if (
            not isinstance(private_key, six.integer_types) or
            not isinstance(x, six.integer_types) or
            not isinstance(y, six.integer_types)
        ):
            raise TypeError("private_key, x and y must be integers.")

        if not isinstance(curve, interfaces.EllipticCurve):
            raise TypeError("curve must provide the EllipticCurve interface.")

        self._private_key = private_key
        self._y = y
        self._x = x
        self._curve = curve

    @classmethod
    def generate(cls, curve, backend):
        return backend.generate_ecdsa_private_key(curve)

    def signer(self, signature_algorithm, backend):
        return signature_algorithm.signer(self, backend)

    @property
    def key_size(self):
        return self._curve.key_size

    @property
    def private_key(self):
        return self._private_key

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def curve(self):
        return self._curve

    def public_key(self):
        return EllipticCurvePublicKey(self._x, self._y, self._curve)
