"""Local conftest for session tests.

Overrides the root _mock_platform fixture which sets sys.platform to 'linux',
causing os.getuid() errors on Windows when pytest creates temp directories.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _mock_platform():
    """No-op override: don't mock platform in session tests."""
    pass
