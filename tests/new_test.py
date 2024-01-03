import asyncio
from pathlib import Path
import re
import json
from unittest.mock import MagicMock

import aiopenapi3
import httpx

import pytest
import pytest_asyncio

from aiopenapi3.extra import Reduce
from aiopenapi3.loader import RedirectLoader

from aiopenapi3_redfish.client import Config, Client
from aiopenapi3_redfish.clinic import RedfishDocument, PayloadAnnotations, ExposeResponseHeaders
from aiopenapi3_redfish.Oem.Dell.clinic import (
    Document as OemDocument,
    Init as OemInit,
    Task as OemTask,
    ExportSystemConfiguration as OemExportSystemConfiguration,
)
from aiopenapi3_redfish.Oem.Dell.oem import DellOem

import aiopenapi3_redfish


@pytest.fixture
def description_documents():
    return Path(aiopenapi3_redfish.__file__).parent / "description_documents"


@pytest.fixture
def config():
    if (p := Path(__file__).parent / "data" / "config.json").exists():
        with p.open("rt") as f:
            r = json.load(f)
    else:
        raise FileNotFoundError(p)
    return r


@pytest.fixture
def target(config):
    return config["target"]


@pytest.fixture
def auth(config):
    return config["username"], config["password"]


def non_validating_https(*args, **kwargs) -> httpx.AsyncClient:
    timeout = httpx.Timeout(timeout=10)
    return httpx.AsyncClient(*args, verify=False, timeout=timeout, **kwargs)


def extended_timeout(*args, **kwargs) -> httpx.AsyncClient:
    timeout = httpx.Timeout(timeout=60)
    return httpx.AsyncClient(*args, verify=False, timeout=timeout, **kwargs)


@pytest_asyncio.fixture
async def client(description_documents, target, auth):
    username, password = auth
    config = Config(
        target=(t := target),
        username=username,
        password=password,
        plugins=[
            RedfishDocument(t),
            PayloadAnnotations(),
            ExposeResponseHeaders(),
            OemDocument(t),
            #            OemInit(),
            Reduce(
                #
                # ServiceRoot
                #
                ("/redfish/v1", ["get"]),
                #
                # AccountService
                #
                ("/redfish/v1/AccountService", ["get"]),
                ("/redfish/v1/AccountService/Accounts", ["get"]),
                ("/redfish/v1/AccountService/Accounts/{ManagerAccountId}", ["get", "patch"]),
                #
                # CertificateService
                #
                ("/redfish/v1/CertificateService", ["get"]),
                (re.compile(r"^/redfish/v1/CertificateService/Actions/.*$"), ["post"]),
                #
                # EventService
                #
                ("/redfish/v1/EventService", ["get", "patch"]),
                ("/redfish/v1/EventService/Subscriptions", ["get", "post"]),
                ("/redfish/v1/EventService/Subscriptions/{EventDestinationId}", ["delete", "get", "patch"]),
                ("/redfish/v1/EventService/Actions/EventService.SubmitTestEvent", ["post"]),
                (
                    "/redfish/v1/EventService/Subscriptions/{EventDestinationId}/Actions/EventDestination.ResumeSubscription",
                    ["post"],
                ),
                ("/redfish/v1/SSE", ["get"]),
                #
                # Managers
                #
                ("/redfish/v1/Managers", ["get"]),
                ("/redfish/v1/Managers/{ManagerId}", ["get"]),
                (re.compile(r"^/redfish/v1/Managers/{ManagerId}/Actions/.*$"), ["post"]),
                ("/redfish/v1/Managers/{ManagerId}/Actions/Oem/EID_674_Manager.ExportSystemConfiguration", ["post"]),
                #
                # DellAttributes
                #
                ("/redfish/v1/Managers/{ManagerId}/Oem/Dell/DellAttributes/{DellAttributesId}", ["get", "patch"]),
                #
                # SessionService
                #
                ("/redfish/v1/SessionService", ["get"]),
                ("/redfish/v1/SessionService/Sessions", ["get", "post"]),
                ("/redfish/v1/SessionService/Sessions/{SessionId}", ["get", "delete"]),
                #
                # TaskService
                #
                ("/redfish/v1/TaskService", ["get"]),
                ("/redfish/v1/TaskService/Tasks", ["get"]),
                ("/redfish/v1/TaskService/Tasks/{TaskId}", ["get", "delete"]),
                #
                # TelemetryService
                #
                ("/redfish/v1/TelemetryService", ["get"]),
                #
                # UpdateService
                #
                ("/redfish/v1/UpdateService", ["get"]),
            ),
            OemTask(),
            OemExportSystemConfiguration(),
        ],
        locations=[
            RedirectLoader((v := description_documents / "dell" / "iDRAC_6.10.00.00_A00")),
            RedirectLoader(v / "OpenAPI"),
            RedirectLoader(description_documents / "swordfish-v1.2.4a"),
        ],
        cache=Path("/tmp/test_new.pickle"),
        session_factory=non_validating_https,
    )
    client = Client(config)
    client._oem = DellOem()
    await client.ainit()
    return client


@pytest.mark.asyncio
async def test_new_Client(client):
    action = client.UpdateService["#UpdateService.SimpleUpdate"]
    action = client.UpdateService.Oem["DellUpdateService.v1_1_0#DellUpdateService.Install"]

    action = client.TelemetryService["#TelemetryService.SubmitTestMetricReport"]

    idx = 1
    async for i in client.AccountService.Accounts.list():
        if i.UserName == "root":
            break
        idx += 1

    root = await client.AccountService.Accounts.index(idx)
    return None


@pytest.mark.asyncio
async def test_Manager(client):
    manager = client.Manager
    action = manager["#Manager.Reset"]
    assert action is not None

    action = manager.Oem["#DellManager.ResetToDefaults"]
    assert action is not None

    return None


@pytest.mark.asyncio
async def test_SessionService(client, auth):
    session = await client.SessionService.createSession()
    client.api.authenticate(None, basicAuth=client.config.auth)

    await client.SessionService.Sessions.refresh()
    async for s in client.SessionService.Sessions.list():
        await s.delete()

    with pytest.raises(RedfishException):
        await session.delete()

    with pytest.raises(RedfishException):
        async for s in client.SessionService.Sessions.list(skip_errors=False):
            await s.delete()


@pytest.mark.asyncio
async def test_Action_CertificateService_GenerateCSR(client: aiopenapi3_redfish.Client):
    action = client.CertificateService["#CertificateService.GenerateCSR"]
    data = action.data.model_validate(
        dict(
            CertificateCollection={
                "@odata.id": "/redfish/v1/Managers/iDRAC.Embedded.1/NetworkProtocol/HTTPS/Certificates"
            },
            Country="DE",
            State="Berlin",
            City="Berlin",
            Organization="Spare",
            OrganizationalUnit="Time",
            CommonName="bmc-400.example.org",
        )
    )

    client.api._session_factory = extended_timeout

    r = await action(data=data.model_dump(exclude_unset=True, by_alias=True))

    client.api._session_factory = None


@pytest.mark.asyncio
async def test_Action_EID_674_Manager_ExportSystemConfiguration(client: aiopenapi3_redfish.AsyncClient):
    r = await client.Manager.Oem["#OemManager.ExportSystemConfiguration"].export()
    r = await client.TaskService.wait_for(r.Id)
    payload = r.Messages[0].root.Message
    assert payload.startswith("<SystemConfiguration")


@pytest.mark.asyncio
async def test_EventService_SSE(client, capsys):
    client.api._session_factory = extended_timeout

    async def sendtestevent():
        for i in range(3):
            action = client.EventService["#EventService.SubmitTestEvent"]
            data = action.data.model_validate(dict(EventType="Alert", MessageId="AMP0300"))
            r = await action(data=data.model_dump(exclude_unset=True, by_alias=True))
            asyncio.sleep(5)

    task = asyncio.create_task(sendtestevent())

    async def process():
        data = b""
        while True:
            data += yield
            lines = data.split(b"\n")
            if lines[-1] == b"":
                data = b""
            else:
                data = lines[-1]
                lines = lines[:-1]
            for l in lines:
                with capsys.disabled():
                    print(l)

    p = process()
    await p.asend(None)

    req = client.api._[(client.EventService.ServerSentEventUri, "get")]
    headers, schema_, session, result = await req.stream()
    l = 0
    async for i in result.aiter_bytes():
        await p.asend(i)
        l += 1
        if l > 2:
            break
    await task

    return None


@pytest.mark.asyncio
async def test_DellAttributes(client, capsys):
    oem = client.Manager.Links.Oem
    obj = oem
    assert obj
    obj = oem.Dell
    assert obj
    obj = oem.Dell.DellAttributes
    async for i in oem.Dell.DellAttributes.list():
        print(i)
    return None


def test_DellAttributesLocal():
    from aiopenapi3 import OpenAPI
    import yarl
    from aiopenapi3_redfish.Oem.Dell.oem import DellAttributes

    api = OpenAPI.cache_load(Path("/tmp/test_new.pickle"))
    data = json.loads((Path(__file__).parent / "data" / "iDRAC.Embedded.1.json").read_text())
    DA = (
        api._documents[yarl.URL("/redfish/v1/Schemas/DellAttributes.v1_0_0.yaml")]
        .components.schemas["DellAttributes_v1_0_0_DellAttributes"]
        .get_type()
    )

    obj = DellAttributes(None, DA.model_validate(data))
    root = obj.filter('.Users.[] | select(.UserName == "root")').first()
    assert root["Privilege"] == DellAttributes.Permissions(511).value

    enabled = obj.filter('.Users.[] | select(.Enable == "Enabled")').all()
    assert len(enabled) == 1

    ntp = obj.filter('.NTPConfigGroup."1"')
    wanted = {"NTP1": "ntp.example.org", "NTPEnable": "Enabled", "NTPMaxDist": 16}
    return None


@pytest.mark.asyncio
async def test_Accounts(client, capsys):
    async for account in client.AccountService.Accounts.list():
        if account.Enabled == False:
            continue
        if account.UserName == "root":
            break
    else:
        raise KeyError(account)

    r = await account.setPassword(account._client.api._security["basicAuth"][1])
    assert r

    r = await client.AccountService.Accounts.index(4)
    #    assert r.Enabled is False
    v = await r.patch({"Enabled": not r.Enabled, "UserName": "debug", "Password": "mercury4111111"})
    assert v.Enabled != r.Enabled

    await r.patch({"Enabled": False})
