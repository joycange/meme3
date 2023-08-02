// This file is dual licensed under the terms of the Apache License, Version
// 2.0, and the BSD License. See the LICENSE file in the root of this repository
// for complete details.

use std::str::FromStr;

/// A `DNSName` is an `asn1::IA5String` with additional invariant preservations
/// per [RFC 5280 4.2.1.6], which in turn uses the preferred name syntax defined
/// in [RFC 1034 3.5] and amended in [RFC 1123 2.1].
///
/// Non-ASCII domain names (i.e., internationalized names) must be pre-encoded;
/// comparisons are case-insensitive.
///
/// [RFC 5280 4.2.1.6]: https://datatracker.ietf.org/doc/html/rfc5280#section-4.2.1.6
/// [RFC 1034 3.5]: https://datatracker.ietf.org/doc/html/rfc1034#section-3.5
/// [RFC 1123 2.1]: https://datatracker.ietf.org/doc/html/rfc1123#section-2.1
///
/// ```rust
/// # use cryptography_x509_validation::types::DNSName;
/// assert_eq!(DNSName::new("foo.com").unwrap(), DNSName::new("FOO.com").unwrap());
/// ```
#[derive(Debug)]
pub struct DNSName<'a>(asn1::IA5String<'a>);

impl<'a> DNSName<'a> {
    pub fn new(value: &'a str) -> Option<Self> {
        // Domains cannot be empty and must (practically)
        // be less than 253 characters (255 in RFC 1034's octet encoding).
        if value.is_empty() || value.len() > 253 {
            None
        } else {
            for label in value.split('.') {
                // Individual labels cannot be empty; cannot exceed 63 characters;
                // cannot start or end with `-`.
                // NOTE: RFC 1034's grammar prohibits consecutive hyphens, but these
                // are used as part of the IDN prefix (e.g. `xn--`)'; we allow them here.
                if label.is_empty()
                    || label.len() > 63
                    || label.starts_with('-')
                    || label.ends_with('-')
                {
                    return None;
                }

                // Labels must only contain `a-zA-Z0-9-`.
                if !label.chars().all(|c| c.is_ascii_alphanumeric() || c == '-') {
                    return None;
                }
            }
            asn1::IA5String::new(value).map(Self)
        }
    }

    pub fn as_str(&self) -> &'a str {
        self.0.as_str()
    }

    /// Return this `DNSName`'s parent domain, if it has one.
    ///
    /// ```rust
    /// # use cryptography_x509_validation::types::DNSName;
    /// let domain = DNSName::new("foo.example.com").unwrap();
    /// assert_eq!(domain.parent().unwrap().as_str(), "example.com");
    /// ```
    pub fn parent(&self) -> Option<Self> {
        match self.as_str().split_once('.') {
            Some((_, parent)) => Self::new(parent),
            None => None,
        }
    }
}

impl PartialEq for DNSName<'_> {
    fn eq(&self, other: &Self) -> bool {
        // DNS names are always case-insensitive.
        self.as_str().eq_ignore_ascii_case(other.as_str())
    }
}

/// A `DNSPattern` represents a subset of the domain name wildcard matching
/// behavior defined in [RFC 6125 6.4.3]. In particular, all DNS patterns
/// must either be exact matches (post-normalization) *or* a single wildcard
/// matching a full label in the left-most label position. Partial label matching
/// (e.g. `f*o.example.com`) is not supported, nor is non-left-most matching
/// (e.g. `foo.*.example.com`).
///
/// [RFC 6125 6.4.3]: https://datatracker.ietf.org/doc/html/rfc6125#section-6.4.3
#[derive(Debug, PartialEq)]
pub enum DNSPattern<'a> {
    Exact(DNSName<'a>),
    Wildcard(DNSName<'a>),
}

impl<'a> DNSPattern<'a> {
    pub fn new(pat: &'a str) -> Option<Self> {
        if let Some(pat) = pat.strip_prefix("*.") {
            DNSName::new(pat).map(Self::Wildcard)
        } else {
            DNSName::new(pat).map(Self::Exact)
        }
    }

    pub fn matches(&self, name: &DNSName) -> bool {
        match self {
            Self::Exact(pat) => pat == name,
            Self::Wildcard(pat) => match name.parent() {
                Some(ref parent) => pat == parent,
                // No parent means we have a single label; wildcards cannot match single labels.
                None => false,
            },
        }
    }
}

#[derive(Debug, PartialEq)]
pub enum IPAddress {
    V4(std::net::Ipv4Addr),
    V6(std::net::Ipv6Addr),
}

/// TODO
impl IPAddress {
    pub fn from_std(addr: std::net::IpAddr) -> Self {
        match addr {
            std::net::IpAddr::V4(a) => Self::V4(a),
            std::net::IpAddr::V6(a) => Self::V6(a),
        }
    }

    pub fn from_str(s: &str) -> Option<Self> {
        std::net::IpAddr::from_str(s).ok().map(Self::from_std)
    }

    pub fn from_bytes(b: &[u8]) -> Option<Self> {
        match b.len() {
            4 => {
                let b: [u8; 4] = b.try_into().ok()?;
                Some(Self::from_std(std::net::IpAddr::from(b)))
            }
            16 => {
                let b: [u8; 16] = b.try_into().ok()?;
                Some(Self::from_std(std::net::IpAddr::from(b)))
            }
            _ => None,
        }
    }

    /// Parses the octets of an IP address as a mask. If the mask is well-formed,
    /// i.e. has only one contiguous block of 1 bits starting from the MSB, a prefix
    /// is returned.
    pub fn as_prefix(&self) -> Option<u8> {
        match self {
            Self::V4(a) => {
                let data = u32::from_be_bytes(a.octets());
                let (leading, total) = (data.leading_ones(), data.count_ones());
                if leading != total {
                    None
                } else {
                    Some(leading as u8)
                }
            }
            Self::V6(a) => {
                let data = u128::from_be_bytes(a.octets());
                let (leading, total) = (data.leading_ones(), data.count_ones());
                if leading != total {
                    None
                } else {
                    Some(leading as u8)
                }
            }
        }
    }

    /// TODO
    pub fn mask(&self, prefix: u8) -> Self {
        match self {
            Self::V4(a) => {
                let masked = u32::from_be_bytes(a.octets()) & !((1u32 << prefix) - 1);
                Self::from_bytes(&masked.to_be_bytes()).unwrap()
            }
            Self::V6(a) => {
                let masked = u128::from_be_bytes(a.octets()) & !((1u128 << prefix) - 1);
                Self::from_bytes(&masked.to_be_bytes()).unwrap()
            }
        }
    }
}

#[derive(Debug, PartialEq)]
pub struct IPRange {
    address: IPAddress,
    prefix: u8,
}

/// TODO
impl IPRange {
    pub fn from_bytes(b: &[u8]) -> Option<Self> {
        let slice_idx = match b.len() {
            8 => 4,
            32 => 16,
            _ => return None,
        };

        let prefix = IPAddress::from_bytes(&b[slice_idx..])?.as_prefix()?;
        Some(IPRange {
            address: IPAddress::from_bytes(&b[..slice_idx])?.mask(prefix),
            prefix,
        })
    }

    /// TODO
    pub fn matches(&self, addr: &IPAddress) -> bool {
        self.address == addr.mask(self.prefix)
    }
}

#[cfg(test)]
mod tests {
    use crate::types::{DNSName, DNSPattern, IPAddress, IPRange};

    #[test]
    fn test_dnsname_debug_trait() {
        // Just to get coverage on the `Debug` derive.
        assert_eq!(
            "DNSName(IA5String(\"example.com\"))",
            format!("{:?}", DNSName::new("example.com").unwrap())
        );
    }

    #[test]
    fn test_dnsname_new() {
        assert_eq!(DNSName::new(""), None);
        assert_eq!(DNSName::new("."), None);
        assert_eq!(DNSName::new(".."), None);
        assert_eq!(DNSName::new(".a."), None);
        assert_eq!(DNSName::new("a.a."), None);
        assert_eq!(DNSName::new(".a"), None);
        assert_eq!(DNSName::new("a."), None);
        assert_eq!(DNSName::new("a.."), None);
        assert_eq!(DNSName::new(" "), None);
        assert_eq!(DNSName::new("\t"), None);
        assert_eq!(DNSName::new(" whitespace "), None);
        assert_eq!(DNSName::new("white. space"), None);
        assert_eq!(DNSName::new("!badlabel!"), None);
        assert_eq!(DNSName::new("bad!label"), None);
        assert_eq!(DNSName::new("goodlabel.!badlabel!"), None);
        assert_eq!(DNSName::new("-foo.bar.example.com"), None);
        assert_eq!(DNSName::new("foo-.bar.example.com"), None);
        assert_eq!(DNSName::new("foo.-bar.example.com"), None);
        assert_eq!(DNSName::new("foo.bar-.example.com"), None);
        assert_eq!(DNSName::new(&"a".repeat(64)), None);
        assert_eq!(DNSName::new("⚠️"), None);

        let long_valid_label = "a".repeat(63);
        let long_name = std::iter::repeat(long_valid_label)
            .take(5)
            .collect::<Vec<_>>()
            .join(".");
        assert_eq!(DNSName::new(&long_name), None);

        assert_eq!(
            DNSName::new(&"a".repeat(63)).unwrap().as_str(),
            "a".repeat(63)
        );
        assert_eq!(DNSName::new("example.com").unwrap().as_str(), "example.com");
        assert_eq!(
            DNSName::new("123.example.com").unwrap().as_str(),
            "123.example.com"
        );
        assert_eq!(DNSName::new("EXAMPLE.com").unwrap().as_str(), "EXAMPLE.com");
        assert_eq!(DNSName::new("EXAMPLE.COM").unwrap().as_str(), "EXAMPLE.COM");
        assert_eq!(
            DNSName::new("xn--bcher-kva.example").unwrap().as_str(),
            "xn--bcher-kva.example"
        );
    }

    #[test]
    fn test_dnsname_equality() {
        assert_ne!(
            DNSName::new("foo.example.com").unwrap(),
            DNSName::new("example.com").unwrap()
        );

        // DNS name comparisons are case insensitive.
        assert_eq!(
            DNSName::new("EXAMPLE.COM").unwrap(),
            DNSName::new("example.com").unwrap()
        );
        assert_eq!(
            DNSName::new("ExAmPLe.CoM").unwrap(),
            DNSName::new("eXaMplE.cOm").unwrap()
        );
    }

    #[test]
    fn test_dnsname_parent() {
        assert_eq!(DNSName::new("localhost").unwrap().parent(), None);
        assert_eq!(
            DNSName::new("example.com").unwrap().parent().unwrap(),
            DNSName::new("com").unwrap()
        );
        assert_eq!(
            DNSName::new("foo.example.com").unwrap().parent().unwrap(),
            DNSName::new("example.com").unwrap()
        );
    }

    #[test]
    fn test_dnspattern_new() {
        assert_eq!(DNSPattern::new("*"), None);
        assert_eq!(DNSPattern::new("*."), None);
        assert_eq!(DNSPattern::new("f*o.example.com"), None);
        assert_eq!(DNSPattern::new("*oo.example.com"), None);
        assert_eq!(DNSPattern::new("fo*.example.com"), None);
        assert_eq!(DNSPattern::new("foo.*.example.com"), None);
        assert_eq!(DNSPattern::new("*.foo.*.example.com"), None);

        assert_eq!(
            DNSPattern::new("example.com").unwrap(),
            DNSPattern::Exact(DNSName::new("example.com").unwrap())
        );
        assert_eq!(
            DNSPattern::new("*.example.com").unwrap(),
            DNSPattern::Wildcard(DNSName::new("example.com").unwrap())
        );
    }

    #[test]
    fn test_dnspattern_matches() {
        let exactly_localhost = DNSPattern::new("localhost").unwrap();
        let any_localhost = DNSPattern::new("*.localhost").unwrap();
        let exactly_example_com = DNSPattern::new("example.com").unwrap();
        let any_example_com = DNSPattern::new("*.example.com").unwrap();

        // Exact patterns match only the exact name.
        assert!(exactly_localhost.matches(&DNSName::new("localhost").unwrap()));
        assert!(exactly_localhost.matches(&DNSName::new("LOCALHOST").unwrap()));
        assert!(exactly_example_com.matches(&DNSName::new("example.com").unwrap()));
        assert!(exactly_example_com.matches(&DNSName::new("EXAMPLE.com").unwrap()));
        assert!(!exactly_example_com.matches(&DNSName::new("foo.example.com").unwrap()));

        // Wildcard patterns match any subdomain, but not the parent or nested subdomains.
        assert!(any_example_com.matches(&DNSName::new("foo.example.com").unwrap()));
        assert!(any_example_com.matches(&DNSName::new("bar.example.com").unwrap()));
        assert!(any_example_com.matches(&DNSName::new("BAZ.example.com").unwrap()));
        assert!(!any_example_com.matches(&DNSName::new("example.com").unwrap()));
        assert!(!any_example_com.matches(&DNSName::new("foo.bar.example.com").unwrap()));
        assert!(!any_example_com.matches(&DNSName::new("foo.bar.baz.example.com").unwrap()));
        assert!(!any_localhost.matches(&DNSName::new("localhost").unwrap()));
    }

    #[test]
    fn test_ipaddress_from_str() {
        assert_ne!(IPAddress::from_str("192.168.1.1"), None)
    }

    #[test]
    fn test_iprange_from_bytes() {
        // 192.168.1.1/16
        let ipv4_with_extra = b"\xc0\xa8\x01\x01\xff\xff\x00\x00";
        assert_ne!(IPRange::from_bytes(ipv4_with_extra), None);

        // 192.168.0.0/16
        let ipv4_masked = b"\xc0\xa8\x00\x00\xff\xff\x00\x00";
        assert_eq!(
            IPRange::from_bytes(ipv4_with_extra),
            IPRange::from_bytes(ipv4_masked)
        );
    }

    #[test]
    fn test_iprange_matches() {
        // 192.168.1.1/16
        let data_ipv4 = b"\xc0\xa8\x01\x01\xff\xff\x00\x00";
        let range = IPRange::from_bytes(data_ipv4).unwrap();

        assert!(range.matches(&IPAddress::from_str("192.168.0.50").unwrap()));
    }

    #[test]
    fn test_iprange_bad_masks() {
        // 192.168.1.1, mask 255.254.255.0
        let bad_mask_one_bit = b"\xc0\xa8\x01\x01\xff\xfe\xff\x00";
        // 192.168.1.1, mask 255.252.255.0
        let bad_mask_many_bits = b"\xc0\xa8\x01\x01\xff\xfc\xff\x00";
        // 192.168.1.1, mask 0.255.255.0
        let bad_mask_octet = b"\xc0\xa8\x01\x01\x00\xff\xff\xff";

        assert_eq!(IPRange::from_bytes(bad_mask_one_bit), None);
        assert_eq!(IPRange::from_bytes(bad_mask_many_bits), None);
        assert_eq!(IPRange::from_bytes(bad_mask_octet), None);
    }
}
