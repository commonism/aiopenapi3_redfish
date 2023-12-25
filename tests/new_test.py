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
from aiopenapi3_redfish.Oem.Dell.clinic import Document as OemDocument
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
                #
                # SessionService
                #
                ("/redfish/v1/SessionService", ["get"]),
                ("/redfish/v1/SessionService/Sessions", ["get", "post"]),
                ("/redfish/v1/SessionService/Sessions/{SessionId}", ["get", "delete"]),
                #
                # TelemetryService
                #
                ("/redfish/v1/TelemetryService", ["get"]),
                #
                # UpdateService
                #
                ("/redfish/v1/UpdateService", ["get"]),
            ),
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
    client._oem.connect(DellOem)
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
async def test_SessionService(client):
    await client.SessionService.createSession()
    async for session in client.SessionService.Sessions.list():
        try:
            await session.delete()
        except aiopenapi3.ResponseSchemaError as e:
            pass


@pytest.mark.asyncio
async def test_Action_CertificateService_GenerateCSR(client: aiopenapi3_redfish.Client):
    action = client.CertificateService["#CertificateService.GenerateCSR"]
    req = action._client.api.createRequest((action._v, "post"))
    data = req.data.get_type().model_validate(
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

    r = await req(data=data.model_dump(exclude_unset=True, by_alias=True))

    client.api._session_factory = None


@pytest.mark.asyncio
async def test_EventService_SSE(client, capsys):
    client.api._session_factory = extended_timeout

    async def sendtestevent():
        for i in range(3):
            action = client.EventService["#EventService.SubmitTestEvent"]
            req = action._client.api.createRequest((action._v, "post"))
            data = req.data.get_type().model_validate(dict(EventType="Alert", MessageId="AMP0300"))
            r = await req(data=data.model_dump(exclude_unset=True, by_alias=True))
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
