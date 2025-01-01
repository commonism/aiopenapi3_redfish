import sys
import io
import zipfile

import httpx

import pytest
import pathlib


@pytest.fixture
def description_documents():
    return pathlib.Path("/tmp/")


@pytest.mark.skipif(sys.version_info < (3, 12), reason="requires python3.12 or higher")
def test_DSP8010(description_documents):
    if not (p := description_documents / "DSP8010" / "2024.3").exists():
        p.mkdir(parents=True, exist_ok=True)

    zip = zipfile.Path(
        zipfile.ZipFile(
            io.BytesIO(
                httpx.get("https://www.dmtf.org/sites/default/files/standards/documents/DSP8010_2024.3.zip").content
            )
        )
    )

    if (sd := (zip / "DSP8010_2024.3")).exists() and sd.is_dir():
        zip = sd

    for i in zip.glob("openapi/*.yaml"):
        (p / i.name).write_text(i.read_text())


@pytest.mark.skipif(sys.version_info < (3, 12), reason="requires python3.12 or higher")
def test_Swordfish(description_documents):
    if not (p := description_documents / "Swordfish" / "v1.2.7").exists():
        p.mkdir(parents=True, exist_ok=True)

    zip = zipfile.Path(
        zipfile.ZipFile(
            io.BytesIO(
                httpx.get(
                    "https://www.snia.org/sites/default/files/technical-work/swordfish/release/v1.2.7/zip/Swordfish_v1.2.7.zip"
                ).content
            )
        )
    )
    schema = zipfile.Path(io.BytesIO((zip / "Swordfish_v1.2.7_Schema.zip").read_bytes()))

    for i in schema.glob("yaml/*.yaml"):
        (p / i.name).write_text(i.read_text())
