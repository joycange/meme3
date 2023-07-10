// This file is dual licensed under the terms of the Apache License, Version
// 2.0, and the BSD License. See the LICENSE file in the root of this repository
// for complete details.

use std::collections::HashSet;

use crate::common;
use crate::crl;
use crate::name;

pub type RawExtensions<'a> = common::Asn1ReadableOrWritable<
    'a,
    asn1::SequenceOf<'a, Extension<'a>>,
    asn1::SequenceOfWriter<'a, Extension<'a>, Vec<Extension<'a>>>,
>;

/// An invariant-enforcing wrapper for `RawExtensions`.
///
/// In particular, an `Extensions` cannot be constructed from a `RawExtensions`
/// that contains duplicated extensions (by OID).
pub struct Extensions<'a, 'b>(Option<&'b RawExtensions<'a>>);

impl<'a, 'b> Extensions<'a, 'b> {
    /// Create an `Extensions` from the given `RawExtensions`.
    ///
    /// Returns an `Err` variant containing the first duplicated extension's
    /// OID, if there are any duplicates.
    pub fn from_raw_extensions(
        raw: Option<&'b RawExtensions<'a>>,
    ) -> Result<Self, asn1::ObjectIdentifier> {
        match raw {
            Some(raw_exts) => {
                let mut seen_oids = HashSet::new();

                for ext in raw_exts.unwrap_read().clone() {
                    if !seen_oids.insert(ext.extn_id.clone()) {
                        return Err(ext.extn_id);
                    }
                }

                Ok(Self(Some(raw_exts)))
            }
            None => Ok(Self(None)),
        }
    }

    /// Retrieves the extension identified by the given OID,
    /// or None if the extension is not present (or no extensions are present).
    pub fn get_extension(&self, oid: &asn1::ObjectIdentifier) -> Option<Extension> {
        self.iter().find(|ext| &ext.extn_id == oid)
    }

    /// Returns a reference to the underlying extensions.
    pub fn as_raw(&self) -> Option<&RawExtensions<'_>> {
        self.0
    }

    /// Returns an iterator over the underlying extensions.
    pub fn iter(&self) -> impl Iterator<Item = Extension> {
        self.as_raw()
            .map(|raw| raw.unwrap_read().clone())
            .into_iter()
            .flatten()
    }
}

#[derive(asn1::Asn1Read, asn1::Asn1Write, PartialEq, Eq, Hash, Clone)]
pub struct Extension<'a> {
    pub extn_id: asn1::ObjectIdentifier,
    #[default(false)]
    pub critical: bool,
    pub extn_value: &'a [u8],
}

impl<'a> Extension<'a> {
    pub fn value<T: asn1::Asn1Readable<'a>>(&'a self) -> asn1::ParseResult<T> {
        asn1::parse_single(self.extn_value)
    }
}

#[derive(asn1::Asn1Read, asn1::Asn1Write)]
pub struct PolicyConstraints {
    #[implicit(0)]
    pub require_explicit_policy: Option<u64>,
    #[implicit(1)]
    pub inhibit_policy_mapping: Option<u64>,
}

#[derive(asn1::Asn1Read, asn1::Asn1Write)]
pub struct AccessDescription<'a> {
    pub access_method: asn1::ObjectIdentifier,
    pub access_location: name::GeneralName<'a>,
}

pub type SequenceOfAccessDescriptions<'a> = common::Asn1ReadableOrWritable<
    'a,
    asn1::SequenceOf<'a, AccessDescription<'a>>,
    asn1::SequenceOfWriter<'a, AccessDescription<'a>, Vec<AccessDescription<'a>>>,
>;

// Needed due to clippy type complexity warning.
type SequenceOfPolicyQualifiers<'a> = common::Asn1ReadableOrWritable<
    'a,
    asn1::SequenceOf<'a, PolicyQualifierInfo<'a>>,
    asn1::SequenceOfWriter<'a, PolicyQualifierInfo<'a>, Vec<PolicyQualifierInfo<'a>>>,
>;

#[derive(asn1::Asn1Read, asn1::Asn1Write)]
pub struct PolicyInformation<'a> {
    pub policy_identifier: asn1::ObjectIdentifier,
    pub policy_qualifiers: Option<SequenceOfPolicyQualifiers<'a>>,
}

#[derive(asn1::Asn1Read, asn1::Asn1Write)]
pub struct PolicyQualifierInfo<'a> {
    pub policy_qualifier_id: asn1::ObjectIdentifier,
    pub qualifier: Qualifier<'a>,
}

#[derive(asn1::Asn1Read, asn1::Asn1Write)]
pub enum Qualifier<'a> {
    CpsUri(asn1::IA5String<'a>),
    UserNotice(UserNotice<'a>),
}

#[derive(asn1::Asn1Read, asn1::Asn1Write)]
pub struct UserNotice<'a> {
    pub notice_ref: Option<NoticeReference<'a>>,
    pub explicit_text: Option<DisplayText<'a>>,
}

#[derive(asn1::Asn1Read, asn1::Asn1Write)]
pub struct NoticeReference<'a> {
    pub organization: DisplayText<'a>,
    pub notice_numbers: common::Asn1ReadableOrWritable<
        'a,
        asn1::SequenceOf<'a, asn1::BigUint<'a>>,
        asn1::SequenceOfWriter<'a, asn1::BigUint<'a>, Vec<asn1::BigUint<'a>>>,
    >,
}

// DisplayText also allows BMPString, which we currently do not support.
#[allow(clippy::enum_variant_names)]
#[derive(asn1::Asn1Read, asn1::Asn1Write)]
pub enum DisplayText<'a> {
    IA5String(asn1::IA5String<'a>),
    Utf8String(asn1::Utf8String<'a>),
    // Not validated due to certificates with UTF-8 in VisibleString. See PR #8884
    VisibleString(common::UnvalidatedVisibleString<'a>),
    BmpString(asn1::BMPString<'a>),
}

// Needed due to clippy type complexity warning.
pub type SequenceOfSubtrees<'a> = common::Asn1ReadableOrWritable<
    'a,
    asn1::SequenceOf<'a, GeneralSubtree<'a>>,
    asn1::SequenceOfWriter<'a, GeneralSubtree<'a>, Vec<GeneralSubtree<'a>>>,
>;

#[derive(asn1::Asn1Read, asn1::Asn1Write)]
pub struct NameConstraints<'a> {
    #[implicit(0)]
    pub permitted_subtrees: Option<SequenceOfSubtrees<'a>>,

    #[implicit(1)]
    pub excluded_subtrees: Option<SequenceOfSubtrees<'a>>,
}

#[derive(asn1::Asn1Read, asn1::Asn1Write)]
pub struct GeneralSubtree<'a> {
    pub base: name::GeneralName<'a>,

    #[implicit(0)]
    #[default(0u64)]
    pub minimum: u64,

    #[implicit(1)]
    pub maximum: Option<u64>,
}

#[derive(asn1::Asn1Read, asn1::Asn1Write)]
pub struct MSCertificateTemplate {
    pub template_id: asn1::ObjectIdentifier,
    pub major_version: Option<u32>,
    pub minor_version: Option<u32>,
}

#[derive(asn1::Asn1Read, asn1::Asn1Write)]
pub struct DistributionPoint<'a> {
    #[explicit(0)]
    pub distribution_point: Option<DistributionPointName<'a>>,

    #[implicit(1)]
    pub reasons: crl::ReasonFlags<'a>,

    #[implicit(2)]
    pub crl_issuer: Option<name::SequenceOfGeneralName<'a>>,
}

#[derive(asn1::Asn1Read, asn1::Asn1Write)]
pub enum DistributionPointName<'a> {
    #[implicit(0)]
    FullName(name::SequenceOfGeneralName<'a>),

    #[implicit(1)]
    NameRelativeToCRLIssuer(
        common::Asn1ReadableOrWritable<
            'a,
            asn1::SetOf<'a, common::AttributeTypeValue<'a>>,
            asn1::SetOfWriter<
                'a,
                common::AttributeTypeValue<'a>,
                Vec<common::AttributeTypeValue<'a>>,
            >,
        >,
    ),
}

#[derive(asn1::Asn1Read, asn1::Asn1Write)]
pub struct AuthorityKeyIdentifier<'a> {
    #[implicit(0)]
    pub key_identifier: Option<&'a [u8]>,
    #[implicit(1)]
    pub authority_cert_issuer: Option<name::SequenceOfGeneralName<'a>>,
    #[implicit(2)]
    pub authority_cert_serial_number: Option<asn1::BigUint<'a>>,
}

#[derive(asn1::Asn1Read, asn1::Asn1Write)]
pub struct BasicConstraints {
    #[default(false)]
    pub ca: bool,
    pub path_length: Option<u64>,
}

pub type SubjectAlternativeName<'a> = asn1::SequenceOf<'a, name::GeneralName<'a>>;
pub type ExtendedKeyUsage<'a> = asn1::SequenceOf<'a, asn1::ObjectIdentifier>;

#[derive(Hash, PartialEq, Clone)]
pub struct KeyUsage<'a>(asn1::BitString<'a>);

impl<'a> asn1::SimpleAsn1Readable<'a> for KeyUsage<'a> {
    const TAG: asn1::Tag = asn1::BitString::TAG;

    fn parse_data(data: &'a [u8]) -> asn1::ParseResult<Self> {
        asn1::BitString::parse_data(data).map(Self)
    }
}

impl KeyUsage<'_> {
    pub fn zeroed(&self) -> bool {
        self.0.as_bytes().iter().all(|&b| b == 0)
    }

    pub fn digital_signature(&self) -> bool {
        self.0.has_bit_set(0)
    }

    pub fn content_comitment(&self) -> bool {
        self.0.has_bit_set(1)
    }

    pub fn key_encipherment(&self) -> bool {
        self.0.has_bit_set(2)
    }

    pub fn data_encipherment(&self) -> bool {
        self.0.has_bit_set(3)
    }

    pub fn key_agreement(&self) -> bool {
        self.0.has_bit_set(4)
    }

    pub fn key_cert_sign(&self) -> bool {
        self.0.has_bit_set(5)
    }

    pub fn crl_sign(&self) -> bool {
        self.0.has_bit_set(6)
    }

    pub fn encipher_only(&self) -> bool {
        self.0.has_bit_set(7)
    }

    pub fn decipher_only(&self) -> bool {
        self.0.has_bit_set(8)
    }
}

#[cfg(test)]
mod tests {
    use asn1::SequenceOfWriter;

    use crate::oid::{AUTHORITY_KEY_IDENTIFIER_OID, BASIC_CONSTRAINTS_OID};

    use super::{BasicConstraints, Extension, Extensions};

    #[test]
    fn test_get_extension() {
        let bc = BasicConstraints {
            ca: true,
            path_length: Some(3),
        };
        let extension = Extension {
            extn_id: BASIC_CONSTRAINTS_OID,
            critical: true,
            extn_value: &asn1::write_single(&bc).unwrap(),
        };
        let extensions = SequenceOfWriter::new(vec![extension]);

        let der = asn1::write_single(&extensions).unwrap();
        let raw = asn1::parse_single(&der).unwrap();

        let extensions: Extensions = Extensions::from_raw_extensions(Some(&raw)).unwrap();

        assert!(&extensions.get_extension(&BASIC_CONSTRAINTS_OID).is_some());
        assert!(&extensions
            .get_extension(&AUTHORITY_KEY_IDENTIFIER_OID)
            .is_none());
    }

    #[test]
    fn test_extensions_iter() {
        let bc = BasicConstraints {
            ca: true,
            path_length: Some(3),
        };
        let extension = Extension {
            extn_id: BASIC_CONSTRAINTS_OID,
            critical: true,
            extn_value: &asn1::write_single(&bc).unwrap(),
        };
        let extensions = SequenceOfWriter::new(vec![extension]);

        let der = asn1::write_single(&extensions).unwrap();
        let parsed = asn1::parse_single(&der).unwrap();

        let extensions: Extensions = Extensions::from_raw_extensions(Some(&parsed)).unwrap();

        let extension_list: Vec<_> = extensions.iter().collect();
        assert_eq!(extension_list.len(), 1);
    }

    #[test]
    fn test_extension_value() {
        let bc = BasicConstraints {
            ca: true,
            path_length: Some(3),
        };
        let extension = Extension {
            extn_id: BASIC_CONSTRAINTS_OID,
            critical: true,
            extn_value: &asn1::write_single(&bc).unwrap(),
        };

        let extracted: BasicConstraints = extension.value().unwrap();
        assert_eq!(bc.ca, extracted.ca);
        assert_eq!(bc.path_length, extracted.path_length);
    }
}
