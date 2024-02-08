# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.

from __future__ import annotations

import typing

from cryptography.hazmat.bindings._rust import x509 as rust_x509
from cryptography.x509.base import Certificate
from cryptography.x509.extensions import Extension, SubjectAlternativeName
from cryptography.x509.general_name import DNSName, IPAddress

__all__ = [
    "Store",
    "Subject",
    "VerifiedClient",
    "ClientVerifier",
    "ServerVerifier",
    "PolicyBuilder",
    "VerificationError",
]

Store = rust_x509.Store
Subject = typing.Union[DNSName, IPAddress]
VerifiedClient = tuple[Extension[SubjectAlternativeName], list[Certificate]]
ClientVerifier = rust_x509.ClientVerifier
ServerVerifier = rust_x509.ServerVerifier
PolicyBuilder = rust_x509.PolicyBuilder
VerificationError = rust_x509.VerificationError
