import logging
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
import yarl
from aiopenapi3.loader import RedirectLoader

import aiopenapi3_redfish
import aiopenapi3_redfish.errors
from aiopenapi3_redfish.client import Config, AsyncClient
from aiopenapi3_redfish.clinic import (
    RedfishDocument,
    PayloadAnnotations,
    ExposeResponseHeaders,
    NullableRefs,
)
from aiopenapi3_redfish.oem import Oem, Detour, Mapping
from aiopenapi3_redfish.entities import Defaults
from aiopenapi3_redfish.serviceroot import AsyncServiceRoot


class MockMessage_v1_2_6(aiopenapi3_redfish.clinic.Message):
    @aiopenapi3_redfish.clinic.Parsed("/redfish/v1/AccountService/Accounts/{ManagerAccountId}", method=["get"])
    def dr_ManagerAccount(self, ctx: "aiopenapi3.plugin.Message.Context"):
        if (k := "AccountTypes") not in ctx.parsed:
            ctx.parsed[k] = []
        return ctx


@pytest_asyncio.fixture(scope="session")
async def client_(description_documents):
    target = "http://localhost:5000/redfish/v1/openapi.yaml"
    username, password = ("", "")
    config = Config(
        target=(t := target),
        username=username,
        password=password,
        plugins=[
            RedfishDocument(t),
            PayloadAnnotations(),
            NullableRefs(),
            ExposeResponseHeaders(),
            MockMessage_v1_2_6(),
        ],
        locations=[
            RedirectLoader(description_documents / "Swordfish" / "v1.2.7"),
            RedirectLoader(v := description_documents / "DSP8010" / "2024.3"),
        ],
        cache=Path("/tmp/test_new.pickle"),
    )
    api = AsyncClient.createAPI(config)
    client = AsyncClient(config, api)
    return client


@Detour("/redfish/v1")
@Detour("#ServiceRoot..ServiceRoot")
class MinimalServiceRoot(AsyncServiceRoot):
    async def asyncInit(self):
        await super().asyncInit("/AccountService")
        return self


class AccountsOnly(Oem):
    detour = [MinimalServiceRoot]


log = logging.getLogger("aiopenapi3_redfish.tests")


def get_mockups():
    import html5lib

    data = httpx.get("https://swordfishmockups.com/")
    kw = {"namespaceHTMLElements": False}
    root = html5lib.parse(data.content, treebuilder="lxml", **kw)
    urls = [
        yarl.URL(i) for i in root.xpath("""//a[@id and contains(@href, ".swordfishmockups.com/redfish/v1")]/@href""")
    ]
    return urls


def mockups_session_factory(*args, **kwargs) -> httpx.AsyncClient:
    timeout = httpx.Timeout(timeout=60)
    return httpx.AsyncClient(*args, verify=False, timeout=timeout, **kwargs, follow_redirects=True)


@pytest.mark.asyncio
async def test_Task(caplog, client_):
    import logging

    caplog.set_level(logging.WARNING, logger="httpx")
    caplog.set_level(logging.WARNING, logger="httpcore")
    caplog.set_level(logging.INFO, logger="urllib3")
    caplog.set_level(logging.INFO, logger="aiopenapi3_redfish.AsyncTaskSet")

    from aiopenapi3_redfish.tasks import AsyncTaskSet, AsyncTask

    class TestTask(AsyncTask):
        async def produce(self):
            for url in get_mockups():
                yield url

        async def consume(self, url: yarl.URL):
            log.debug(url)
            auth = ("Administrator", "Password")

            api = client_.api.clone(url)
            api._session_factory = mockups_session_factory
            config = aiopenapi3_redfish.Config(target=str(url), username=auth[0], password=auth[1])
            c = aiopenapi3_redfish.client.AsyncClient(config, api)
            api.authenticate(None, basicAuth=(auth[0], auth[1]))

            c._mapping = Mapping(oem=AccountsOnly(), defaults=Defaults())

            try:
                await c.asyncInit()
            except Exception as e:
                c.log.exception(e)
                c.log.info(f"FAIL init")
                return

            try:
                async for account in c.AccountService.Accounts.list():
                    if account.UserName == auth[0]:
                        break
                else:
                    raise KeyError(auth[0])
            except Exception as e:
                c.log.info(f"FAIL")
                c.log.exception(e)

    c = AsyncTaskSet(TestTask(), num_consumers=4)
    await c.run()
