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

import cffi

from cryptography.hazmat.bindings.utils import binding_available
from cryptography.hazmat.bindings.openssl.binding import Binding


def dummy_initializer():
    ffi = cffi.FFI()
    ffi.verify(source="random text that won't compile")


def test_binding_available():
    assert binding_available(Binding._ensure_ffi_initialized) is True


def test_binding_unavailable():
    assert binding_available(dummy_initializer) is False
