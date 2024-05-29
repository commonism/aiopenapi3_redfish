from pathlib import Path

import pytest

import aiopenapi3_redfish


@pytest.fixture(scope="session")
def description_documents():
    return Path(aiopenapi3_redfish.__file__).parent / "description_documents"


@pytest.fixture
def log(caplog):
    import logging

    caplog.set_level(logging.INFO, logger="httpcore")
    caplog.set_level(logging.INFO, logger="httpx")
