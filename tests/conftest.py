from pathlib import Path

import pytest

import aiopenapi3_redfish


@pytest.fixture(scope="session")
def description_documents():
    return Path(aiopenapi3_redfish.__file__).parent / "description_documents"
