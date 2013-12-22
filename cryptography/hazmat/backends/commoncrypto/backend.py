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

import sys

import cffi

from cryptography import utils
from cryptography.exceptions import UnsupportedAlgorithm, InvalidTag
from cryptography.hazmat.backends.interfaces import (
    CipherBackend, HashBackend, HMACBackend
)
from cryptography.hazmat.primitives import constant_time, interfaces
from cryptography.hazmat.primitives.ciphers.algorithms import (
    AES, Blowfish, TripleDES, ARC4, CAST5
)
from cryptography.hazmat.primitives.ciphers.modes import (
    CBC, CTR, ECB, OFB, CFB, GCM
)


@utils.register_interface(CipherBackend)
@utils.register_interface(HashBackend)
@utils.register_interface(HMACBackend)
class Backend(object):
    """
    CommonCrypto API wrapper.
    """
    _modules = [
        "common_cryptor",
        "common_digest",
        "common_hmac",
    ]

    ffi = None
    lib = None

    def __init__(self):
        self._ensure_ffi_initialized()

        self._cipher_registry = {}
        self._register_default_ciphers()
        self.hash_mappings = {
            "md5": {
                "object": "CC_MD5_CTX *",
                "init": self.lib.CC_MD5_Init,
                "update": self.lib.CC_MD5_Update,
                "final": self.lib.CC_MD5_Final},
            "sha1": {
                "object": "CC_SHA1_CTX *",
                "init": self.lib.CC_SHA1_Init,
                "update": self.lib.CC_SHA1_Update,
                "final": self.lib.CC_SHA1_Final},
            "sha224": {
                "object": "CC_SHA256_CTX *",
                "init": self.lib.CC_SHA224_Init,
                "update": self.lib.CC_SHA224_Update,
                "final": self.lib.CC_SHA224_Final},
            "sha256": {
                "object": "CC_SHA256_CTX *",
                "init": self.lib.CC_SHA256_Init,
                "update": self.lib.CC_SHA256_Update,
                "final": self.lib.CC_SHA256_Final},
            "sha384": {
                "object": "CC_SHA512_CTX *",
                "init": self.lib.CC_SHA384_Init,
                "update": self.lib.CC_SHA384_Update,
                "final": self.lib.CC_SHA384_Final},
            "sha512": {
                "object": "CC_SHA512_CTX *",
                "init": self.lib.CC_SHA512_Init,
                "update": self.lib.CC_SHA512_Update,
                "final": self.lib.CC_SHA512_Final},
        }

    @classmethod
    def _ensure_ffi_initialized(cls):
        if cls.ffi is not None and cls.lib is not None:
            return

        ffi = cffi.FFI()
        includes = []
        functions = []
        macros = []
        customizations = []
        for name in cls._modules:
            module_name = "cryptography.hazmat.backends.commoncrypto." + name
            __import__(module_name)
            module = sys.modules[module_name]

            ffi.cdef(module.TYPES)

            macros.append(module.MACROS)
            functions.append(module.FUNCTIONS)
            includes.append(module.INCLUDES)
            customizations.append(module.CUSTOMIZATIONS)

        # loop over the functions & macros after declaring all the types
        # so we can set interdependent types in different files and still
        # have them all defined before we parse the funcs & macros
        for func in functions:
            ffi.cdef(func)
        for macro in macros:
            ffi.cdef(macro)

        # We include functions here so that if we got any of their definitions
        # wrong, the underlying C compiler will explode. In C you are allowed
        # to re-declare a function if it has the same signature. That is:
        #   int foo(int);
        #   int foo(int);
        # is legal, but the following will fail to compile:
        #   int foo(int);
        #   int foo(short);
        lib = ffi.verify(
            source="\n".join(includes + functions + customizations),
            libraries=[],
        )

        cls.ffi = ffi
        cls.lib = lib

    def create_hmac_ctx(self, key, algorithm):
        return _HMACContext(self, key, algorithm)

    def hash_supported(self, algorithm):
        return algorithm.name in self.hash_mappings

    def create_hash_ctx(self, algorithm):
        return _HashContext(self, algorithm)

    def cipher_supported(self, cipher, mode):
        try:
            self._cipher_registry[type(cipher), type(mode)]
        except KeyError:
            return False
        return True

    def register_cipher_adapter(self, cipher_cls, mode_cls, adapter):
        if (cipher_cls, mode_cls) in self._cipher_registry:
            raise ValueError("Duplicate registration for: {0} {1}".format(
                cipher_cls, mode_cls)
            )
        self._cipher_registry[cipher_cls, mode_cls] = adapter

    def _register_default_ciphers(self):
        for mode_cls in [CBC, ECB, CFB, OFB, CTR, GCM]:
            self.register_cipher_adapter(
                AES,
                mode_cls,
                GetCipherModeEnum()
            )
        for mode_cls in [CBC, CFB, OFB]:
            self.register_cipher_adapter(
                TripleDES,
                mode_cls,
                GetCipherModeEnum()
            )
        for mode_cls in [CBC, CFB, OFB, ECB]:
            self.register_cipher_adapter(
                Blowfish,
                mode_cls,
                GetCipherModeEnum()
            )
        self.register_cipher_adapter(
            CAST5,
            ECB,
            GetCipherModeEnum()
        )
        self.register_cipher_adapter(
            ARC4,
            type(None),
            GetCipherModeEnum()
        )

    def create_symmetric_encryption_ctx(self, cipher, mode):
        if isinstance(mode, GCM):
            return _GCMCipherContext(
                self, cipher, mode, _CipherContext._ENCRYPT
            )
        else:
            return _CipherContext(self, cipher, mode, _CipherContext._ENCRYPT)

    def create_symmetric_decryption_ctx(self, cipher, mode):
        if isinstance(mode, GCM):
            return _GCMCipherContext(
                self, cipher, mode, _CipherContext._DECRYPT
            )
        else:
            return _CipherContext(self, cipher, mode, _CipherContext._DECRYPT)


class GetCipherModeEnum(object):
    def __call__(self, backend, cipher, mode):
        try:
            cipher_enum = {
                AES: backend.lib.kCCAlgorithmAES128,
                TripleDES: backend.lib.kCCAlgorithm3DES,
                Blowfish: backend.lib.kCCAlgorithmBlowfish,
                ARC4: backend.lib.kCCAlgorithmRC4,
                CAST5: backend.lib.kCCAlgorithmCAST,
            }[type(cipher)]
        except KeyError:
            raise UnsupportedAlgorithm

        try:
            mode_enum = {
                ECB: backend.lib.kCCModeECB,
                CBC: backend.lib.kCCModeCBC,
                CTR: backend.lib.kCCModeCTR,
                CFB: backend.lib.kCCModeCFB,
                OFB: backend.lib.kCCModeOFB,
                GCM: 11,
                type(None): backend.lib.kCCModeRC4,
            }[type(mode)]
        except KeyError:
            raise UnsupportedAlgorithm

        return (cipher_enum, mode_enum)


@utils.register_interface(interfaces.CipherContext)
class _CipherContext(object):
    _ENCRYPT = 0  # kCCEncrypt
    _DECRYPT = 1  # kCCDecrypt

    def __init__(self, backend, cipher, mode, operation):
        self._backend = backend
        self._cipher = cipher
        self._mode = mode
        self._operation = operation
        # bytes_processed is needed to work around rdar://15589470, a bug where
        # kCCAlignmentError is not raised when not supplying block-aligned data
        self._bytes_processed = 0
        if (isinstance(cipher, interfaces.BlockCipherAlgorithm) and not
                isinstance(mode, (OFB, CFB, CTR))):
            self._byte_block_size = cipher.block_size // 8
        else:
            self._byte_block_size = 1

        registry = self._backend._cipher_registry
        try:
            adapter = registry[type(cipher), type(mode)]
        except KeyError:
            raise UnsupportedAlgorithm

        cipher_enum, mode_enum = adapter(self._backend, cipher, mode)
        ctx = self._backend.ffi.new("CCCryptorRef *")
        ctx[0] = self._backend.ffi.gc(
            ctx[0], self._backend.lib.CCCryptorRelease
        )

        if isinstance(mode, interfaces.ModeWithInitializationVector):
            iv_nonce = mode.initialization_vector
        elif isinstance(mode, interfaces.ModeWithNonce):
            iv_nonce = mode.nonce
        else:
            iv_nonce = self._backend.ffi.NULL

        if isinstance(mode, CTR):
            mode_option = self._backend.lib.kCCModeOptionCTR_BE
        else:
            mode_option = 0

        res = self._backend.lib.CCCryptorCreateWithMode(
            operation,
            mode_enum, cipher_enum,
            self._backend.lib.ccNoPadding, iv_nonce,
            cipher.key, len(cipher.key),
            self._backend.ffi.NULL, 0, 0, mode_option, ctx)
        assert res == self._backend.lib.kCCSuccess

        self._ctx = ctx

    def update(self, data):
        # manually count bytes processed to handle block alignment
        self._bytes_processed += len(data)
        buf = self._backend.ffi.new(
            "unsigned char[]", len(data) + self._byte_block_size - 1)
        outlen = self._backend.ffi.new("size_t *")
        res = self._backend.lib.CCCryptorUpdate(
            self._ctx[0], data, len(data), buf,
            len(data) + self._byte_block_size - 1, outlen)
        assert res == self._backend.lib.kCCSuccess
        return self._backend.ffi.buffer(buf)[:outlen[0]]

    def finalize(self):
        # raise error if block alignment is wrong since commoncrypto won't
        if self._bytes_processed % self._byte_block_size:
            raise ValueError(
                "The length of the provided data is not a multiple of "
                "the block length"
            )
        buf = self._backend.ffi.new("unsigned char[]", self._byte_block_size)
        outlen = self._backend.ffi.new("size_t *")
        res = self._backend.lib.CCCryptorFinal(
            self._ctx[0], buf, len(buf), outlen)
        assert res == self._backend.lib.kCCSuccess
        res = self._backend.lib.CCCryptorRelease(self._ctx[0])
        assert res == self._backend.lib.kCCSuccess
        return self._backend.ffi.buffer(buf)[:outlen[0]]


@utils.register_interface(interfaces.AEADCipherContext)
@utils.register_interface(interfaces.AEADEncryptionContext)
class _GCMCipherContext(_CipherContext):
    def __init__(self, backend, cipher, mode, operation):
        super(_GCMCipherContext, self).__init__(
            backend, cipher, mode, operation
        )
        self._tag = None
        iv_nonce = mode.initialization_vector
        res = self._backend.lib.CCCryptorGCMAddIV(
            self._ctx[0], iv_nonce, len(iv_nonce)
        )
        assert res == self._backend.lib.kCCSuccess
        # must make at least one empty AAD call for GCM to work for
        # some bizarre reason.
        self.authenticate_additional_data(b"")
        if operation == self._DECRYPT:
            if not mode.tag or len(mode.tag) < 4:
                raise ValueError("Authentication tag must be provided and "
                                 "be 4 bytes or longer when decrypting")
        else:
            if mode.tag:
                raise ValueError("Authentication tag must be None when "
                                 "encrypting")

    def update(self, data):
        buf = self._backend.ffi.new("unsigned char[]", len(data))
        if self._operation == self._ENCRYPT:
            res = self._backend.lib.CCCryptorGCMEncrypt(
                self._ctx[0], data, len(data), buf)
        else:
            res = self._backend.lib.CCCryptorGCMDecrypt(
                self._ctx[0], data, len(data), buf)

        assert res == self._backend.lib.kCCSuccess
        return self._backend.ffi.buffer(buf)[:len(data)]

    def finalize(self):
        tag_size = self._cipher.block_size // 8
        tag_buf = self._backend.ffi.new("unsigned char[]", tag_size)
        tag_len = self._backend.ffi.new("size_t *", tag_size)
        res = backend.lib.CCCryptorGCMFinal(self._ctx[0], tag_buf, tag_len)
        assert res == self._backend.lib.kCCSuccess
        res = self._backend.lib.CCCryptorRelease(self._ctx[0])
        assert res == self._backend.lib.kCCSuccess
        self._tag = self._backend.ffi.buffer(tag_buf)[:tag_size]
        if self._operation == self._DECRYPT and not constant_time.bytes_eq(
            self._tag[:len(self._mode.tag)], self._mode.tag
        ):
            raise InvalidTag
        return b""

    def authenticate_additional_data(self, data):
        res = self._backend.lib.CCCryptorGCMAddAAD(
            self._ctx[0], data, len(data)
        )
        assert res == self._backend.lib.kCCSuccess

    @property
    def tag(self):
        return self._tag


@utils.register_interface(interfaces.HashContext)
class _HashContext(object):
    def __init__(self, backend, algorithm, ctx=None):
        self._algorithm = algorithm
        self._backend = backend

        if ctx is None:
            try:
                mapping = self._backend.hash_mappings[algorithm.name]
            except KeyError:
                raise UnsupportedAlgorithm(
                    "{0} is not a supported hash on this backend".format(
                        algorithm.name)
                )
            ctx = self._backend.ffi.new(mapping["object"])
            # init/update/final ALWAYS return 1
            mapping["init"](ctx)

        self._ctx = ctx

    def copy(self):
        mapping = self._backend.hash_mappings[self._algorithm.name]
        new_ctx = self._backend.ffi.new(mapping["object"])
        new_ctx[0] = self._ctx[0]  # supposed to be legit per C90?

        return _HashContext(self._backend, self._algorithm, ctx=new_ctx)

    def update(self, data):
        mapping = self._backend.hash_mappings[self._algorithm.name]
        mapping["update"](self._ctx, data, len(data))

    def finalize(self):
        mapping = self._backend.hash_mappings[self._algorithm.name]
        buf = self._backend.ffi.new("unsigned char[]",
                                    self._algorithm.digest_size)
        mapping["final"](buf, self._ctx)
        return self._backend.ffi.buffer(buf)[:]


@utils.register_interface(interfaces.HashContext)
class _HMACContext(object):
    def __init__(self, backend, key, algorithm, ctx=None):
        self._algorithm = algorithm
        self._backend = backend
        self.supported_algorithms = {
            "md5": backend.lib.kCCHmacAlgMD5,
            "sha1": backend.lib.kCCHmacAlgSHA1,
            "sha224": backend.lib.kCCHmacAlgSHA224,
            "sha256": backend.lib.kCCHmacAlgSHA256,
            "sha384": backend.lib.kCCHmacAlgSHA384,
            "sha512": backend.lib.kCCHmacAlgSHA512,
        }
        if ctx is None:
            ctx = self._backend.ffi.new("CCHmacContext *")
            try:
                alg = self.supported_algorithms[algorithm.name]
            except KeyError:
                raise UnsupportedAlgorithm(
                    "{0} is not a supported hash on this backend".format(
                        algorithm.name)
                )

            self._backend.lib.CCHmacInit(ctx, alg, key, len(key))

        self._ctx = ctx
        self._key = key

    def copy(self):
        copied_ctx = self._backend.ffi.new("CCHmacContext *")
        copied_ctx[0] = self._ctx[0]  # supposed to be legit per C90?
        return _HMACContext(
            self._backend, self._key, self._algorithm, ctx=copied_ctx
        )

    def update(self, data):
        self._backend.lib.CCHmacUpdate(self._ctx, data, len(data))

    def finalize(self):
        buf = self._backend.ffi.new("unsigned char[]",
                                    self._algorithm.digest_size)
        self._backend.lib.CCHmacFinal(self._ctx, buf)
        return self._backend.ffi.buffer(buf)[:]


backend = Backend()
