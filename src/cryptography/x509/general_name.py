# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.


import abc
import ipaddress
import typing
from email.utils import parseaddr

from cryptography.x509.name import Name
from cryptography.x509.oid import ObjectIdentifier


_GENERAL_NAMES = {
    0: "otherName",
    1: "rfc822Name",
    2: "dNSName",
    3: "x400Address",
    4: "directoryName",
    5: "ediPartyName",
    6: "uniformResourceIdentifier",
    7: "iPAddress",
    8: "registeredID",
}
_IPADDRESS_TYPES = typing.Union[
    ipaddress.IPv4Address,
    ipaddress.IPv6Address,
    ipaddress.IPv4Network,
    ipaddress.IPv6Network,
]


class UnsupportedGeneralNameType(Exception):
    def __init__(self, msg: str, type: int) -> None:
        super(UnsupportedGeneralNameType, self).__init__(msg)
        self.type = type


class GeneralName(metaclass=abc.ABCMeta):
    @abc.abstractproperty
    def value(self) -> typing.Any:
        """
        Return the value of the object
        """


class RFC822Name(GeneralName):
<<<<<<< HEAD
    def __init__(self, value: str) -> None:
=======
    def __init__(self, value: str):
>>>>>>> b813e816e2871e5f9ab2f101ee94713f8b3e95b0
        if isinstance(value, str):
            try:
                value.encode("ascii")
            except UnicodeEncodeError:
                raise ValueError(
                    "RFC822Name values should be passed as an A-label string. "
                    "This means unicode characters should be encoded via "
                    "a library like idna."
                )
        else:
            raise TypeError("value must be string")

        name, address = parseaddr(value)
        if name or not address:
            # parseaddr has found a name (e.g. Name <email>) or the entire
            # value is an empty string.
            raise ValueError("Invalid rfc822name value")

        self._value = value

    @property
    def value(self) -> str:
        return self._value

    @classmethod
    def _init_without_validation(cls, value: str) -> "RFC822Name":
        instance = cls.__new__(cls)
        instance._value = value
        return instance

    def __repr__(self) -> str:
        return "<RFC822Name(value={0!r})>".format(self.value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RFC822Name):
            return NotImplemented

        return self.value == other.value

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash(self.value)


class DNSName(GeneralName):
<<<<<<< HEAD
    def __init__(self, value: str) -> None:
=======
    def __init__(self, value: str):
>>>>>>> b813e816e2871e5f9ab2f101ee94713f8b3e95b0
        if isinstance(value, str):
            try:
                value.encode("ascii")
            except UnicodeEncodeError:
                raise ValueError(
                    "DNSName values should be passed as an A-label string. "
                    "This means unicode characters should be encoded via "
                    "a library like idna."
                )
        else:
            raise TypeError("value must be string")

        self._value = value

    @property
    def value(self) -> str:
        return self._value

    @classmethod
    def _init_without_validation(cls, value: str) -> "DNSName":
        instance = cls.__new__(cls)
        instance._value = value
        return instance

    def __repr__(self) -> str:
        return "<DNSName(value={0!r})>".format(self.value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DNSName):
            return NotImplemented

        return self.value == other.value

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash(self.value)


class UniformResourceIdentifier(GeneralName):
<<<<<<< HEAD
    def __init__(self, value: str) -> None:
=======
    def __init__(self, value: str):
>>>>>>> b813e816e2871e5f9ab2f101ee94713f8b3e95b0
        if isinstance(value, str):
            try:
                value.encode("ascii")
            except UnicodeEncodeError:
                raise ValueError(
                    "URI values should be passed as an A-label string. "
                    "This means unicode characters should be encoded via "
                    "a library like idna."
                )
        else:
            raise TypeError("value must be string")

        self._value = value

    @property
    def value(self) -> str:
        return self._value

    @classmethod
    def _init_without_validation(
        cls, value: str
    ) -> "UniformResourceIdentifier":
        instance = cls.__new__(cls)
        instance._value = value
        return instance

    def __repr__(self) -> str:
        return "<UniformResourceIdentifier(value={0!r})>".format(self.value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UniformResourceIdentifier):
            return NotImplemented

        return self.value == other.value

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash(self.value)


class DirectoryName(GeneralName):
<<<<<<< HEAD
    def __init__(self, value: Name) -> None:
=======
    def __init__(self, value: Name):
>>>>>>> b813e816e2871e5f9ab2f101ee94713f8b3e95b0
        if not isinstance(value, Name):
            raise TypeError("value must be a Name")

        self._value = value

    @property
    def value(self) -> Name:
        return self._value

    def __repr__(self) -> str:
        return "<DirectoryName(value={})>".format(self.value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DirectoryName):
            return NotImplemented

        return self.value == other.value

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash(self.value)


class RegisteredID(GeneralName):
<<<<<<< HEAD
    def __init__(self, value: ObjectIdentifier) -> None:
=======
    def __init__(self, value: ObjectIdentifier):
>>>>>>> b813e816e2871e5f9ab2f101ee94713f8b3e95b0
        if not isinstance(value, ObjectIdentifier):
            raise TypeError("value must be an ObjectIdentifier")

        self._value = value

    @property
    def value(self) -> ObjectIdentifier:
        return self._value

    def __repr__(self) -> str:
        return "<RegisteredID(value={})>".format(self.value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RegisteredID):
            return NotImplemented

        return self.value == other.value

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash(self.value)


class IPAddress(GeneralName):
<<<<<<< HEAD
    def __init__(self, value: _IPADDRESS_TYPES) -> None:
=======
    def __init__(
        self,
        value: typing.Union[
            ipaddress.IPv4Address,
            ipaddress.IPv6Address,
            ipaddress.IPv4Network,
            ipaddress.IPv6Network,
        ],
    ):
>>>>>>> b813e816e2871e5f9ab2f101ee94713f8b3e95b0
        if not isinstance(
            value,
            (
                ipaddress.IPv4Address,
                ipaddress.IPv6Address,
                ipaddress.IPv4Network,
                ipaddress.IPv6Network,
            ),
        ):
            raise TypeError(
                "value must be an instance of ipaddress.IPv4Address, "
                "ipaddress.IPv6Address, ipaddress.IPv4Network, or "
                "ipaddress.IPv6Network"
            )

        self._value = value

    @property
<<<<<<< HEAD
    def value(self) -> _IPADDRESS_TYPES:
=======
    def value(
        self,
    ) -> typing.Union[
        ipaddress.IPv4Address,
        ipaddress.IPv6Address,
        ipaddress.IPv4Network,
        ipaddress.IPv6Network,
    ]:
>>>>>>> b813e816e2871e5f9ab2f101ee94713f8b3e95b0
        return self._value

    def __repr__(self) -> str:
        return "<IPAddress(value={})>".format(self.value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, IPAddress):
            return NotImplemented

        return self.value == other.value

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash(self.value)


class OtherName(GeneralName):
<<<<<<< HEAD
    def __init__(self, type_id: ObjectIdentifier, value: bytes) -> None:
=======
    def __init__(self, type_id: ObjectIdentifier, value: bytes):
>>>>>>> b813e816e2871e5f9ab2f101ee94713f8b3e95b0
        if not isinstance(type_id, ObjectIdentifier):
            raise TypeError("type_id must be an ObjectIdentifier")
        if not isinstance(value, bytes):
            raise TypeError("value must be a binary string")

        self._type_id = type_id
        self._value = value

    @property
    def type_id(self) -> ObjectIdentifier:
        return self._type_id
<<<<<<< HEAD

    @property
    def value(self) -> bytes:
        return self._value

=======

    @property
    def value(self) -> bytes:
        return self._value

>>>>>>> b813e816e2871e5f9ab2f101ee94713f8b3e95b0
    def __repr__(self) -> str:
        return "<OtherName(type_id={}, value={!r})>".format(
            self.type_id, self.value
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, OtherName):
            return NotImplemented

        return self.type_id == other.type_id and self.value == other.value

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash((self.type_id, self.value))
