import zipfile
from pathlib import Path

import yarl
import httpx
import json

import pytest
import pytest_asyncio

import aiopenapi3_redfish.serviceroot

from aiopenapi3.loader import RedirectLoader
from aiopenapi3.extra import Reduce
import aiopenapi3.plugin
import aiopenapi3.request

from aiopenapi3_redfish.client import Config, AsyncClient
from aiopenapi3_redfish.errors import RedfishException
from aiopenapi3_redfish.clinic import (
    RedfishDocument,
    PayloadAnnotations,
    ExposeResponseHeaders,
    NullableRefs,
)


@pytest.fixture
def log(caplog):
    import logging

    caplog.set_level(logging.WARNING, logger="httpcore")
    caplog.set_level(logging.WARNING, logger="httpx")


@pytest.fixture(scope="session")
def target():
    return "https://localhost/redfish/v1/openapi.yaml"


@pytest_asyncio.fixture(scope="session")
async def client(api, config, target):
    client = MockClient(config, api)

    from aiopenapi3_redfish.oem import Mapping, Oem
    from aiopenapi3_redfish.entities import Defaults

    client._mapping = Mapping(oem=Oem(), defaults=Defaults())
    return client


@pytest.fixture(scope="session")
def config(description_documents, target):
    username, password = ("1", "1")
    config = Config(
        target=(t := target),
        username=username,
        password=password,
        plugins=[
            RedfishDocument(t),
            PayloadAnnotations(),
            NullableRefs(),
            ExposeResponseHeaders(),
            MockDocument(target),
            #            MockMessage(),
        ],
        locations=[
            RedirectLoader(description_documents / "DSP8010" / "2024.1"),
            RedirectLoader(description_documents / "Swordfish" / "v1.2.6"),
        ],
        cache=Path("/tmp/test_new.pickle"),
    )
    return config


@pytest_asyncio.fixture(scope="session")
async def api(description_documents, config):
    api = AsyncClient.createAPI(config)
    return api


class MockClient(AsyncClient):
    async def _request_send(self, req, parameters, data, context=None, **kwargs):
        url = yarl.URL(req.req.url.format(**parameters))
        assert url.fragment == ""
        f = Path(url.path).relative_to("/redfish/v1")
        p: Path
        if f.name == "":
            p = self.dsp2043 / "index.json"
        else:
            if (d := (self.dsp2043 / f)).exists() and d.is_dir():
                p = self.dsp2043 / f / "index.json"
            else:
                p = self.dsp2043 / f"{f.name}.json"
        data = json.loads(p.read_text())
        r = aiopenapi3.request.RequestBase.Response(headers={}, data=data, result=None)
        try:
            return req.operation.responses["200"].content["application/json"].schema_.model(r.data)
        except Exception as e:
            raise e


class MockDocument(aiopenapi3.plugin.Document):
    def __init__(self, url):
        self._url = url
        super().__init__()

    def parsed(self, ctx: aiopenapi3.plugin.Document.Context) -> aiopenapi3.plugin.Document.Context:
        if Path(ctx.url.path).name == "openapi.yaml":
            ctx.document["paths"]["/redfish/v1/SessionService/Sessions"]["post"]["security"] = []
        return ctx


def dsp2043zip():
    url = yarl.URL("https://www.dmtf.org/sites/default/files/standards/documents/DSP2043_2024.1.zip")

    for i in ["~/www-data", "/tmp/"]:
        if (p := Path(i).expanduser() / Path(url.path).name).exists():
            return zipfile.Path(p)

    with httpx.Client() as f:
        r = f.get(str(url))
        (p := (Path("/tmp/") / url.name)).write_bytes(r.content)
        return zipfile.Path(p)


def pytest_generate_tests(metafunc):
    zipfile = dsp2043zip()
    if "dsp2043" in metafunc.fixturenames and "file" in metafunc.fixturenames:
        names = ["dsp2043", "file"]
        values = []
        ids = []
        #        dsp2043 = list(filter(lambda i: i.is_dir() and i.name.startswith("public-"), zipfile.iterdir()))
        #        for i in dsp2043:
        for info in zipfile.root.infolist():
            if info.is_dir():
                continue
            rfile = (file := Path(info.filename)).relative_to(dsp2043 := file.parts[0])
            if not dsp2043.startswith("public-"):
                continue
            if rfile.parts[0] in {"$metadata", "explorer_config.json"}:
                continue
            if not rfile.name.endswith(".json"):
                continue
            values.append([zipfile / dsp2043, rfile])
            ids.append(f"{dsp2043}::{rfile}")
        metafunc.parametrize(names, values, ids=ids)
    elif "dsp2043" in metafunc.fixturenames:
        values = list(filter(lambda i: i.is_dir() and i.name.startswith("public-"), zipfile.iterdir()))
        ids = [i.name for i in values]
        values = list([i] for i in values)
        names = ["dsp2043"]
        metafunc.parametrize(names, values, ids=ids)


def test_dsp2043(dsp2043):
    with (dsp2043 / "index.json").open("rb") as f:
        data = json.load(f)


class RoutingError(Exception):
    pass


@pytest.mark.xfail
@pytest.mark.asyncio
async def test_dsp2043_file(client, dsp2043, file):
    client.dsp2043 = dsp2043
    await _test_single_file(client, file)


async def _test_single_file(client, file: Path):
    if file.name == "index.json":
        url = file.parent
    else:
        url = file.parent / file.stem

    url = Path("/redfish/v1") / url

    try:
        p, routepath = client.routeOf(str(url))
    except KeyError as e:
        raise RoutingError(url) from e
    req = client.api._[(routepath, "get")]
    return await client._request_send(req, p, None)


@pytest.mark.asyncio
async def test_single_file(client):
    mock = "public-liquid-cooled-server"
    file = "ComponentIntegrity/SS-SPDM-0/index.json"
    client.dsp2043 = dsp2043zip() / mock
    await _test_single_file(client, Path(file))


@pytest.mark.asyncio
async def test_iter(client):
    pages: set[yarl.URL] = set()
    todo = set()

    from typing import Any
    import pydantic

    def _find_links(data: pydantic.BaseModel | list[Any] | dict[str, Any]) -> set[str]:
        links = set()
        if isinstance(data, pydantic.BaseModel) and (v := getattr(data, "odata_id_", None)) is not None:
            links.add(v)
        elif isinstance(data, dict) and (v := data.get("@odata.id", None)) is not None:
            links.add(v)

        if isinstance(data, pydantic.BaseModel):
            for k in sorted(data.model_fields_set):
                v = getattr(data, k)
                if v is None or isinstance(v, (str, int)):
                    continue
                links.update(_find_links(v))
        elif isinstance(data, dict):
            for v in data.values():
                if v is None or isinstance(v, (str, int)):
                    continue
                links.update(_find_links(v))
        elif isinstance(data, list):
            for v in data:
                if v is None or isinstance(v, (str, int)):
                    continue
                links.update(_find_links(v))
        elif isinstance(data, (str, int)):
            pass
        else:
            pass
        return links

    # import collections
    # Page = collections.namedtuple("Page", field_names=["routepath", "parameters", "data", "response"])

    class RoutingError(Exception):
        pass

    async def get(t: yarl.URL):
        try:
            p, routepath = client.routeOf(t)
        except KeyError as e:
            raise RoutingError(t) from e
        req = client.api._[(routepath, "get")]
        return await client._request_send(req, p, None)

    async def visit(t: yarl.URL) -> pydantic.BaseModel | list[Any] | dict[str, Any]:
        try:
            r = await get(t)
            return r
        except aiopenapi3.errors.ResponseSchemaError as rse:
            print(f"{rse.__class__.__name__} {t} {rse}")
            return rse.response.json()
        except aiopenapi3.errors.ResponseError as rer:
            print(f"{rer.__class__.__name__} {t} {rer}")
        except RoutingError as ror:
            print(f"{ror.__class__.__name__} {t} {ror}")
        except KeyError as ke:
            print(f"{ke.__class__.__name__} {t} {ke}")
        except pydantic.ValidationError as ve:
            print(f"{ve.__class__.__name__} {t} {ve}")

    todo |= _find_links(client._serviceroot._v) - pages

    while todo:
        c = todo.pop()
        if (nf := (yarl.URL(c).with_fragment(None) / "")) in pages:
            continue

        r = await visit(nf)
        if r:
            todo |= _find_links(r) - pages - frozenset([nf])

        pages.add(nf)
