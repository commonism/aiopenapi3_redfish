import string
from pathlib import Path
import random

from pathlib import Path


import aiopenapi3
import httpx

import pytest
import pytest_asyncio

from aiopenapi3.extra import Reduce, Cull
from aiopenapi3.loader import RedirectLoader
import aiopenapi3.plugin

from aiopenapi3_redfish.client import Config, AsyncClient
from aiopenapi3_redfish.errors import RedfishException
from aiopenapi3_redfish.clinic import (
    RedfishDocument,
    PayloadAnnotations,
    ExposeResponseHeaders,
    NullableRefs,
)
import pytest
import pytest_asyncio

import yarl
import aiopenapi3_redfish
from aiopenapi3_redfish.errors import RedfishException


class MockDocument(aiopenapi3.plugin.Document):
    def __init__(self, url):
        self._url = url
        super().__init__()

    def parsed(self, ctx: aiopenapi3.plugin.Document.Context) -> aiopenapi3.plugin.Document.Context:
        if Path(ctx.url.path).name == "openapi.yaml":
            ctx.document["paths"]["/redfish/v1/SessionService/Sessions"]["post"]["security"] = []
        return ctx


class MockMessage(aiopenapi3_redfish.clinic.Message):
    @aiopenapi3_redfish.clinic.Parsed("/redfish/v1", method=["get"])
    def dr_ServiceRoot(self, ctx: "aiopenapi3.plugin.Message.Context"):
        ctx.parsed["Links"] = {"Sessions": {"@odata.id": "/redfish/v1/SessionService/Sessions"}}
        return ctx

    @aiopenapi3_redfish.clinic.Parsed("/redfish/v1/SessionService", method=["get"])
    def dr_SessionService(self, ctx: "aiopenapi3.plugin.Message.Context"):
        ctx.parsed["Id"] = "SessionService._.SessionService"

    @aiopenapi3_redfish.clinic.Parsed(
        "/redfish/v1/Systems/{ComputerSystemId}/LogServices/{LogServiceId}/Entries", method=["get"]
    )
    @aiopenapi3_redfish.clinic.Parsed(
        "/redfish/v1/Managers/{ManagerId}/LogServices/{LogServiceId}/Entries", method=["get"]
    )
    def dr_LogServiceEntries(self, ctx: "aiopenapi3.plugin.Message.Context"):
        ctx.parsed["Members"] = [{"@odata.id": i["@odata.id"]} for i in ctx.parsed["Members"]]


@pytest.fixture
def auth():
    return ("root", "123")


@pytest.fixture
def target():
    return "http://localhost:8000/redfish/v1/openapi.yaml"


@pytest_asyncio.fixture
async def client_(description_documents, target, auth, log):
    username, password = auth
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
            MockMessage(),
        ],
        locations=[
            RedirectLoader(v := description_documents / "DSP8010" / "2024.3"),
            RedirectLoader(v / "OpenAPI"),
            RedirectLoader(description_documents / "Swordfish" / "v1.2.7"),
        ],
        cache=Path("/tmp/test_new.pickle"),
    )
    api = AsyncClient.createAPI(config)
    client = AsyncClient(config, api)
    return client


@pytest_asyncio.fixture
async def client(client_, auth):
    def non_validating_https(*args, **kwargs) -> httpx.AsyncClient:
        timeout = httpx.Timeout(timeout=60)
        return httpx.AsyncClient(*args, verify=False, timeout=timeout, **kwargs, follow_redirects=True)

    api = client_.api.clone(url := yarl.URL("http://localhost:8000/redfish/v1/openapi.yaml"))
    api._session_factory = non_validating_https

    api.authenticate(None, basicAuth=(auth[0], auth[1]))
    config = aiopenapi3_redfish.Config(target=url, username=auth[0], password=auth[1])
    c = aiopenapi3_redfish.client.AsyncClient(config, api)

    from aiopenapi3_redfish.oem import Mapping, Oem
    from aiopenapi3_redfish.entities import Defaults

    c._mapping = Mapping(oem=Oem(), defaults=Defaults())

    await c.asyncInit()
    return c


@pytest.mark.asyncio
async def test_SessionService_Sessions_post(client, auth):
    data = {"UserName": auth[0], "Password": auth[1]}
    req = client.api._[("/redfish/v1/SessionService/Sessions", "post")]
    headers, value = await req(data=data, return_headers=True)


@pytest.mark.asyncio
async def test_SessionService_Sessions_get(client, auth):
    r = await client.SessionService.Sessions.index("1")


@pytest.mark.asyncio
async def test_SessionService_Sessions_list(client, auth):
    await client.SessionService.Sessions.refresh()
    async for _ in client.SessionService.Sessions.list():
        continue


@pytest.mark.xfail
@pytest.mark.asyncio
async def test_TaskManager(client):
    async for i in client.TaskService.Tasks.list():
        print(i)


@pytest.mark.asyncio
async def test_Accounts(client, capsys):
    async for account in client.AccountService.Accounts.list():
        if account.Enabled == False:
            continue
        if account.UserName == "Administrator":
            break
    else:
        raise KeyError(account)

    r = await account.setPassword(account._client.api._security["basicAuth"][1])
    assert r

    r = await client.AccountService.Accounts.index(4)
    #    assert r.Enabled is False
    v = await r.patch(
        {
            "Enabled": not r.Enabled,
            "UserName": "debug",
            "Password": "".join(random.choice(string.ascii_letters + string.digits) for _ in range(16)),
        }
    )
    assert v.Enabled != r.Enabled

    await r.patch({"Enabled": False})


@pytest.mark.asyncio
async def test_Inventory(client, capsys):
    chassis = await client.Chassis.index("1U")
    async for iface in chassis.NetworkAdapters.list():
        print(f"{iface.Manufacturer}/{iface.Model}")
        async for port in iface.NetworkPorts.list():
            print(f"\t{port.Id} {port.AssociatedNetworkAddresses} {port.LinkStatus=}")


@pytest.mark.asyncio
async def test_iter(client, capsys):
    pages = {yarl.URL("/redfish/v1")}
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

    async def get(t):
        try:
            p, routepath = client.routeOf(yarl.URL(t))
        except KeyError as e:
            raise RoutingError(t) from e
        req = client.api._[(routepath, "get")]

        r = await req.request(parameters=p, data=None, context=None)
        return r

    async def visit(t) -> pydantic.BaseModel | list[Any] | dict[str, Any]:
        try:
            r = await get(t)
            return r.data
        except aiopenapi3.errors.ResponseSchemaError as rse:
            print(f"{rse.__class__.__name__} {t}")
            print()
            return rse.response.json()
        except aiopenapi3.errors.ResponseError as rer:
            print(f"{rer.__class__.__name__} {t} {rer}")
        except RoutingError as ror:
            print(f"{ror.__class__.__name__} {t} {ror}")
        except KeyError as ke:
            print(f"{ke.__class__.__name__} {t} {ke}")
            return list()

    todo |= _find_links(client._serviceroot._v) - pages

    while todo:
        c = todo.pop()
        if (nf := (yarl.URL(c).with_fragment(None) / "")) in pages:
            continue

        r = await visit(c)
        if r:
            todo |= _find_links(r) - pages - frozenset([nf])

        pages.add(nf)
