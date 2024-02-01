import asyncio
import logging
import string
from pathlib import Path
import re
import json
import random


import aiopenapi3
import httpx

import pytest
import pytest_asyncio

from aiopenapi3.extra import Reduce, Cull
from aiopenapi3.loader import RedirectLoader

from aiopenapi3_redfish.client import Config, AsyncClient
from aiopenapi3_redfish.errors import RedfishException
from aiopenapi3_redfish.clinic import RedfishDocument, PayloadAnnotations, ExposeResponseHeaders
from aiopenapi3_redfish.Oem.Dell.clinic import (
    Document_vX as OemDocumentGenerator,
    Document_v7_00_60_00 as OemDocument,
    Message as OemMessage,
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


@pytest.fixture
def log(caplog):
    import logging

    caplog.set_level(logging.INFO, logger="httpcore")
    caplog.set_level(logging.INFO, logger="httpx")


@pytest_asyncio.fixture
async def client(description_documents, target, auth, log):
    username, password = auth
    config = Config(
        target=(t := target),
        username=username,
        password=password,
        plugins=[
            RedfishDocument(t),
            PayloadAnnotations(),
            ExposeResponseHeaders(),
            #            OemDocumentGenerator(t, description_documents / "dell" / "iDRAC_7.00.60.00_A00"),
            OemDocument(t),
            OemMessage(),
            Reduce(
                # (re.compile(r".*"), ["get", "post", "put", "patch", "delete"]),
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
                # Chassis
                #
                ("/redfish/v1/Chassis", ["get"]),
                ("/redfish/v1/Chassis/{ChassisId}", ["get"]),
                ("/redfish/v1/Chassis/{ChassisId}/NetworkAdapters", ["get"]),
                ("/redfish/v1/Chassis/{ChassisId}/NetworkAdapters/{NetworkAdapterId}", ["get"]),
                ("/redfish/v1/Chassis/{ChassisId}/NetworkAdapters/{NetworkAdapterId}/NetworkPorts", ["get"]),
                (
                    "/redfish/v1/Chassis/{ChassisId}/NetworkAdapters/{NetworkAdapterId}/NetworkPorts/{NetworkPortId}",
                    ["get"],
                ),
                ("/redfish/v1/Chassis/{ChassisId}/NetworkAdapters/{NetworkAdapterId}/NetworkDeviceFunctions", ["get"]),
                (
                    "/redfish/v1/Chassis/{ChassisId}/NetworkAdapters/{NetworkAdapterId}/NetworkDeviceFunctions/{NetworkDeviceFunctionId}",
                    ["get"],
                ),
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
                # Fabrics
                #
                ("/redfish/v1/Fabrics", ["get"]),
                #
                # JobService
                #
                ("/redfish/v1/JobService", ["get"]),
                ("/redfish/v1/JobService/Jobs", ["get", "post"]),
                ("/redfish/v1/JobService/Jobs/{JobId}", ["get", "delete"]),
                ("/redfish/v1/JobService/Jobs/{JobId}/Steps", ["get", "post"]),
                ("/redfish/v1/JobService/Jobs/{JobId}/Steps/{JobId2}", ["get", "delete"]),
                ("/redfish/v1/Managers/{ManagerId}/Oem/Dell/DellJobService", ["get"]),
                ("/redfish/v1/Managers/{ManagerId}/Oem/Dell/Jobs", ["get", "post"]),
                ("/redfish/v1/Managers/{ManagerId}/Oem/Dell/Jobs/{DellJobId}", ["get", "delete"]),
                #
                # LicenseService
                #
                ("/redfish/v1/LicenseService", ["get"]),
                #
                # Managers
                #
                ("/redfish/v1/Managers", ["get"]),
                ("/redfish/v1/Managers/{ManagerId}", ["get"]),
                (re.compile(r"^/redfish/v1/Managers/{ManagerId}/Actions/.*$"), ["post"]),
                ("/redfish/v1/Managers/{ManagerId}/Actions/Oem/EID_674_Manager.ExportSystemConfiguration", ["post"]),
                (re.compile(r"/redfish/v1/Managers/{ManagerId}/Actions/Oem/DellManager\..*$"), ["post"]),
                ("/redfish/v1/Managers/iDRAC.Embedded.1/Actions/Oem/DellManager.SetCustomDefaults", ["post"]),
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
                # Systems
                #
                ("/redfish/v1/Systems", ["get"]),
                ("/redfish/v1/Systems/{ComputerSystemId}", ["get"]),
                (re.compile(r"^/redfish/v1/Systems/{ComputerSystemId}/Actions/ComputerSystem.\S+$"), ["post"]),
                ("/redfish/v1/Systems/{ComputerSystemId}/Oem/Dell/DellSoftwareInstallationService", ["get"]),
                (
                    re.compile(
                        r"^/redfish/v1/Systems/{ComputerSystemId}/Oem/Dell/DellSoftwareInstallationService/Actions/DellSoftwareInstallationService.\S+$"
                    ),
                    ["post"],
                ),
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
                ("/redfish/v1/TelemetryService/Actions/TelemetryService.SubmitTestMetricReport", ["post"]),
                #
                # UpdateService
                #
                ("/redfish/v1/UpdateService", ["get"]),
                ("/redfish/v1/UpdateService/Actions/UpdateService.SimpleUpdate", ["post"]),
                ("/redfish/v1/UpdateService/Actions/Oem/DellUpdateService.Install", ["post"]),
                #
                # Oem Reduce Safehouse
                #
                ("/redfish/oem", ["get"]),
            ),
        ],
        locations=[
            RedirectLoader((v := description_documents / "dell" / "iDRAC_7.00.60.00_A00")),
            RedirectLoader(v / "OpenAPI"),
            RedirectLoader(description_documents / "swordfish-v1.2.4a"),
        ],
        cache=Path("/tmp/test_new.pickle"),
        session_factory=non_validating_https,
    )
    api = AsyncClient.createAPI(config)
    client = AsyncClient(config, api)
    from aiopenapi3_redfish.oem import Mapping
    from aiopenapi3_redfish.entities import Defaults

    client._mapping = Mapping(oem=DellOem(), defaults=Defaults())
    await client.asyncInit()
    return client


@pytest.mark.asyncio
async def test_new_Client(client):
    action = client.UpdateService.Actions["#UpdateService.SimpleUpdate"]
    action = client.UpdateService.Actions.Oem["DellUpdateService.v1_1_0#DellUpdateService.Install"]

    action = client.TelemetryService.Actions["#TelemetryService.SubmitTestMetricReport"]

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
    action = manager.Actions["#Manager.Reset"]
    assert action is not None

    action = manager.Actions.Oem["#DellManager.ResetToDefaults"]
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
async def test_Action_CertificateService_GenerateCSR(client: aiopenapi3_redfish.AsyncClient):
    action = client.CertificateService.Actions["#CertificateService.GenerateCSR"]
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
    r = await client.Manager.Actions.Oem["#OemManager.ExportSystemConfiguration"].export()
    r = await client.TaskService.wait_for(r.Id)
    payload = r.Messages[0].root.Message
    assert payload.startswith("<SystemConfiguration")


@pytest.mark.asyncio
async def test_EventService_SSE(client, capsys):
    client.api._session_factory = extended_timeout

    async def sendtestevent():
        for i in range(3):
            await client.EventService.SubmitTestEvent(EventType="Alert", MessageId="AMP0300")
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
async def test_Oem(client):
    import aiopenapi3_redfish.Oem.Dell.oem

    #    links = client.Manager.Links.Oem
    #    assert isinstance(links, aiopenapi3_redfish.Oem.Dell.oem.ManagerLinksOem)

    actions = client.Manager.Actions.Oem
    assert isinstance(actions, aiopenapi3_redfish.Oem.Dell.oem.ManagerActionsOem)
    return None


@pytest.mark.asyncio
async def test_DellAttributes(client, capsys):
    oem = client.Manager.Links.Oem
    obj = oem
    assert obj
    obj = oem.Dell
    assert obj
    obj = obj.DellAttributes
    async for i in obj.list():
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
    chassis = await client.Chassis.index("System.Embedded.1")
    async for iface in chassis.NetworkAdapters.list():
        print(f"{iface.Manufacturer}/{iface.Model}")
        async for port in iface.NetworkPorts.list():
            print(f"\t{port.Id} {port.AssociatedNetworkAddresses} {port.LinkStatus=}")


@pytest.mark.asyncio
async def test_DellSoftwareInstallationService(client, caplog):
    import logging

    caplog.set_level(logging.WARNING, logger="httpx")
    system = await client.Systems.index("System.Embedded.1")

    dsis = await system.Links.Oem.Dell.DellSoftwareInstallationService.get()
    await dsis.InstallFromRepository()


@pytest.mark.asyncio
async def test_DellSoftwareInstallationService_wait(client, caplog):
    system = await client.Systems.index("System.Embedded.1")
    dsis = await system.Links.Oem.Dell.DellSoftwareInstallationService.get()
    await dsis._awaitInstall()


@pytest.mark.asyncio
async def test_DellSoftwareInstallationServiceGetRepoBasedUpdateList(client, caplog):
    system = await client.Systems.index("System.Embedded.1")
    dsis = await system.Links.Oem.Dell.DellSoftwareInstallationService.get()
    action = dsis.Actions["#DellSoftwareInstallationService.GetRepoBasedUpdateList"]
    data = action.data.model_validate({})
    try:
        r = await action(data=data.model_dump(exclude_unset=True, by_alias=True))
    except aiopenapi3_redfish.errors.RedfishException as e:
        msg = "Unable to complete the operation because the catalog name entered has either unsupported firmware packages or same version installed on the server."
        assert any(True for i in map(lambda x: x.Message, e.value.error.Message_ExtendedInfo_) if msg in i)
    else:
        import xml.etree.ElementTree

        et = xml.etree.ElementTree.fromstring(r.PackageList)
        jids = set(
            filter(lambda x: isinstance(x, str), map(lambda x: x.text, et.findall('.//PROPERTY[@NAME="JobID"]/VALUE')))
        )
        print(jids)
        done, todo, error = await client.JobService.wait_for(*jids)
        for job in done:
            print(f"{job.Id=} {job.JobStatus=} {job.Messages[0].root.MessageId}/{job.Messages[0].root.Message}")


@pytest.mark.asyncio
async def test_Jobs(client, capsys):
    async for job in client.JobService.Jobs.list():
        print(job)
        break
    else:
        raise ValueError("Job not found")

    djs = await client.Manager.Links.Oem.Dell.DellJobService.get()

    r = await client.Manager.Links.Oem.Dell.Jobs.refresh()
    async for job in r.list():
        print(job)
        break
    else:
        raise ValueError("DellJob not found")
