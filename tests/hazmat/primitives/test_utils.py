import pytest

from .utils import (
    encrypt_test, hash_test, long_string_hash_test, hmac_test,
    stream_encryption_test, aead_test,
)


class TestEncryptTest(object):
    def test_skips_if_only_if_returns_false(self):
        with pytest.raises(pytest.skip.Exception) as exc_info:
            encrypt_test(
                None, None, None, None,
                only_if=lambda backend: False,
                skip_message="message!"
            )
        assert exc_info.value.args[0] == "message!"


class TestAEADTest(object):
    def test_skips_if_only_if_returns_false(self):
        with pytest.raises(pytest.skip.Exception) as exc_info:
            aead_test(
                None, None, None, None,
                only_if=lambda backend: False,
                skip_message="message!"
            )
        assert exc_info.value.args[0] == "message!"


class TestHashTest(object):
    def test_skips_if_only_if_returns_false(self):
        with pytest.raises(pytest.skip.Exception) as exc_info:
            hash_test(
                None, None, None,
                only_if=lambda backend: False,
                skip_message="message!"
            )
        assert exc_info.value.args[0] == "message!"


class TestLongHashTest(object):
    def test_skips_if_only_if_returns_false(self):
        with pytest.raises(pytest.skip.Exception) as exc_info:
            long_string_hash_test(
                None, None, None,
                only_if=lambda backend: False,
                skip_message="message!"
            )
        assert exc_info.value.args[0] == "message!"


class TestHMACTest(object):
    def test_skips_if_only_if_returns_false(self):
        with pytest.raises(pytest.skip.Exception) as exc_info:
            hmac_test(
                None, None, None,
                only_if=lambda backend: False,
                skip_message="message!"
            )
        assert exc_info.value.args[0] == "message!"


class TestStreamEncryptionTest(object):
    def test_skips_if_only_if_returns_false(self):
        with pytest.raises(pytest.skip.Exception) as exc_info:
            stream_encryption_test(
                None, None, None,
                only_if=lambda backend: False,
                skip_message="message!"
            )
        assert exc_info.value.args[0] == "message!"
