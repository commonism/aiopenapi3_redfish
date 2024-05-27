import io
import zipfile

import httpx


def test_DSP8010(description_documents):
    if (p := description_documents / "DSP8010" / "2024.1").exists():
        return

    p.mkdir(parents=True, exist_ok=True)

    zip = zipfile.Path(
        zipfile.ZipFile(
            io.BytesIO(
                httpx.get("https://www.dmtf.org/sites/default/files/standards/documents/DSP8010_2024.1.zip").content
            )
        )
    )
    for i in zip.glob("openapi/*.yaml"):
        (p / i.name).write_text(i.read_text())


def test_Swordfish(description_documents):
    if (p := description_documents / "Swordfish" / "v1.2.6").exists():
        return

    p.mkdir(parents=True, exist_ok=True)

    zip = zipfile.Path(
        zipfile.ZipFile(
            io.BytesIO(
                httpx.get(
                    "https://www.snia.org/sites/default/files/technical-work/swordfish/release/v1.2.6/zip/Swordfish_v1.2.6.zip"
                ).content
            )
        )
    )
    schema = zipfile.Path(io.BytesIO((zip / "Swordfish_v1.2.6_Schema.zip").read_bytes()))

    for i in schema.glob("yaml/*.yaml"):
        (p / i.name).write_text(i.read_text())
