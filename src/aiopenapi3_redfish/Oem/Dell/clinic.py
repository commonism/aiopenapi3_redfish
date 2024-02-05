import inspect
import copy
import collections
import yaml
import io
import json

import yarl

import aiopenapi3
import aiopenapi3.plugin

import aiopenapi3_redfish.clinic


class _DocumentBase(aiopenapi3.plugin.Document):
    def __init__(self, url):
        self._url = url
        super().__init__()

    def parsed(self, ctx: aiopenapi3.plugin.Document.Context) -> aiopenapi3.plugin.Document.Context:
        if str(ctx.url) == self._url:
            # mangle the Task refs in the loaded openapi.yaml
            for k, v in ctx.document["paths"].items():
                for o, op in v.items():
                    for code, content in op["responses"].items():
                        if "content" not in content:
                            continue
                        try:
                            s = content["content"]["application/json"]["schema"]
                        except KeyError:
                            continue
                        if "$ref" in s and s["$ref"] == "/redfish/v1/Schemas/Task.v1_6_0.yaml#/components/schemas/Task":
                            s["$ref"] = "/redfish/v1/Schemas/Task.v1_6_0.yaml#/components/schemas/Task_v1_6_0_Task"

            """
            set the PathItems security to X-Auth OR basicAuth instead of X-Auth AND basicAuth
            """
            for k, v in ctx.document["paths"].items():
                for o, op in v.items():
                    if op["security"] == [{"basicAuth": [], "X-Auth": []}]:
                        op["security"] = [{"basicAuth": []}, {"X-Auth": []}]

            data = ctx.document
            """
            DellAttributes Alias
            /redfish/v1/Managers/{ManagerId}/Attributes -> /redfish/v1/Managers/{ManagerId}/Oem/Dell/DellAttributes/{DellAttributesId}
            """
            if "/redfish/v1/Managers/{ManagerId}/Attributes" not in data["paths"]:
                n = data["paths"]["/redfish/v1/Managers/{ManagerId}/Attributes"] = copy.deepcopy(
                    data["paths"]["/redfish/v1/Managers/{ManagerId}/Oem/Dell/DellAttributes/{DellAttributesId}"]
                )
                for op in ["patch", "get"]:
                    del n[op]["operationId"]
                    del n[op]["parameters"][1]

            """
            SSE url
            """
            data = yaml.safe_load(
                io.StringIO(
                    """
paths:
  /redfish/v1/SSE:
    get:
      description: !
      responses:
        '200':
          content:
            text/event-stream:
              schema:
                {}
          description: Server Sent Event Stream
      security:
      - X-Auth: []
      - basicAuth: []
      summary: EventService SSE
      tags:
      - EventService
"""
                )
            )
            ctx.document["paths"].update(data["paths"])

            # inject operation referencing required Schemas
            data = yaml.safe_load(
                io.StringIO(
                    """
paths:
  /redfish/oem:
    get:
      description: !
      responses:
        'default':
          content:
            application/json:
              schema:
                anyOf:
                  - $ref: "/redfish/v1/Schemas/DellOem.yaml#/components/schemas/DellOem_DellOemLinks"
          description: DellOem Links hosts the DellAttributes
"""
                )
            )

            ctx.document["paths"].update(data["paths"])

        return ctx

    def removeInvalidVersions(self, ctx, data):
        """remove invalid (= file is missing) references from anyOf root schemas"""

        root = Path(ctx.url.path).stem

        if "." in root:
            return

        if (versions := data.get(root, None)) is None:
            return

        for name, value in ctx.document["components"]["schemas"].items():
            if "anyOf" not in value:
                continue

            def versionMatch(x):
                u = yarl.URL(x["$ref"])
                return u.path in [f"/redfish/v1/Schemas/{root}.v{version}.yaml" for version in versions]

            value["anyOf"] = list(filter(versionMatch, value["anyOf"]))
        return ctx

    def fixDellManager(self, ctx):
        """
        The DelliDRACCard property defined as odata-v4_idRef instead of DelliDRACCard_DelliDRACCard
        """
        if ctx.url.path.startswith("/redfish/v1/Schemas/DellManager.v"):
            root, _, version = Path(ctx.url.path).stem.partition(".")
            if (e := f"{root}_{version}_{root}") in ctx.document["components"]["schemas"]:
                v = ctx.document["components"]["schemas"][e]["properties"]

                # Fix DelliDRACCard $ref
                assert (
                    v["DelliDRACCard"]["$ref"] == "/redfish/v1/Schemas/odata-v4.yaml#/components/schemas/odata-v4_idRef"
                )
                v["DelliDRACCard"][
                    "$ref"
                ] = "/redfish/v1/Schemas/DelliDRACCard.yaml#/components/schemas/DelliDRACCard_DelliDRACCard"

    def fixResourceHealth(self, ctx):
        """
        Dell uses Unknown for Health when the System is powered off and the value is unknown
        """
        for key in ["Resource_Health", "Resource_State", "Resource_PowerState", "Resource_Status"]:
            try:
                ctx.document["components"]["schemas"][key]["enum"].append("Unknown")
                ctx.document["components"]["schemas"][key]["nullable"] = True
            except Exception:
                pass
            else:
                print(f"patched {key} in {ctx.url} adding Unknown to enum")

    def fixTaskService(self, ctx):
        """
        The TaskService serves as TaskMonitor as well
        It may return data instead of a Task when finished to expose the result

        FIXME not fixed by vendor as of 7.00.60.00
        """
        try:
            pi = ctx.document["paths"]["/redfish/v1/TaskService/Tasks/{TaskId}"]
        except KeyError:
            return ctx

        m = pi["get"]
        if "*/*" not in m["responses"]["200"]["content"]:
            """
            For update, replace, and delete operations …
            After processing of the task is complete, the modified resource may be returned in response to a request to the task monitor URI with the HTTP 200 OK status code.
            """
            m["responses"]["200"]["content"]["*/*"] = {"schema": {}}

        if "201" not in m["responses"]:
            """
            For create operations …
            After processing of the task is complete, the created resource may be returned in response to a request to the task monitor URI with the HTTP 201 Created status code.
            """
            m["responses"]["201"] = {"content": {"*/*": {"schema": {}}}, "description": "the created resource …"}

        if "202" not in m["responses"]:
            """
            12.2 Asynchronous operations

            As long as the operation is in process, the service shall return the HTTP 202 Accepted status code when the client performs a GET request on the task monitor URI.
            """
            m["responses"]["202"] = {
                "content": {"application/json": m["responses"]["200"]["content"]["application/json"]},
                "description": "the pending resource",
            }
        return ctx


class Document_v6_10_00_00(_DocumentBase):
    VERSIONS = dict(
        [
            ("Capacity", ("1_2_0",)),
            ("Certificate", ("1_6_0",)),
            ("Circuit", ("1_6_0",)),
            ("ComputerSystem", ("1_18_0",)),
            ("Control", ("1_1_0",)),
            ("DataProtectionLoSCapabilities", ("1_2_0",)),
            ("DataStorageLoSCapabilities", ("1_2_2",)),
            ("DellAssembly", ("1_0_0",)),
            ("DellBIOSService", ("1_0_0",)),
            ("DellChassis", ("1_0_0",)),
            ("DellController", ("1_4_1",)),
            ("DellControllerBattery", ("1_0_0",)),
            ("DellEnclosure", ("1_1_0",)),
            ("DellEnclosureEMM", ("1_1_0",)),
            ("DellEnclosureFanSensor", ("1_1_0",)),
            ("DellEnclosurePowerSupply", ("1_0_0",)),
            ("DellEnclosureTemperatureSensor", ("1_1_0",)),
            ("DellFC", ("1_4_0",)),
            ("DellFCCapabilities", ("1_0_0",)),
            ("DellFCPortMetrics", ("1_1_1",)),
            ("DellFCStatistics", ("1_0_0",)),
            ("DellFRUAssembly", ("1_1_0",)),
            ("DellGPUSensor", ("1_0_1",)),
            ("DellInfiniBand", ("1_2_0",)),
            ("DellInfiniBandCapabilities", ("1_0_0",)),
            ("DellInfiniBandPortMetrics", ("1_0_0",)),
            ("DellJobService", ("1_2_0",)),
            ("DellLCService", ("1_4_0",)),
            ("DellLicensableDevice", ("1_0_0",)),
            ("DellLicense", ("1_2_0",)),
            ("DellLicenseManagementService", ("1_1_0",)),
            ("DellManager", ("1_3_0",)),
            ("DellManagerAccount", ("1_0_0",)),
            ("DellManagerNetworkProtocol", ("1_0_0",)),
            ("DellMemory", ("1_1_0",)),
            ("DellMetricReport", ("1_0_0",)),
            ("DellMetricReportDefinition", ("1_1_0",)),
            ("DellMetricService", ("1_1_0",)),
            ("DellNIC", ("1_6_0",)),
            ("DellNICCapabilities", ("1_2_0",)),
            ("DellNICPortMetrics", ("1_1_1",)),
            ("DellNetworkTransceiver", ("1_1_0",)),
            ("DellNetworkTransceiverPortMetrics", ("1_0_0",)),
            ("DellNumericSensor", ("1_1_1",)),
            ("DellOSDeploymentService", ("1_1_0",)),
            ("DellOem", ("1_3_0",)),
            ("DellOemEnclosureChassis", ("1_0_0",)),
            ("DellOemStorageController", ("1_0_0",)),
            ("DellPCIeFunction", ("1_4_0",)),
            ("DellPCIeSSD", ("1_7_0",)),
            ("DellPCIeSSDExtender", ("1_0_0",)),
            ("DellPSNumericSensor", ("1_1_0",)),
            ("DellPersistentStorageService", ("1_1_0",)),
            ("DellPhysicalDisk", ("1_6_0",)),
            ("DellPowerSupply", ("1_1_1",)),
            ("DellPowerSupplyView", ("1_3_0",)),
            ("DellPresenceAndStatusSensor", ("1_0_0",)),
            ("DellProcessor", ("1_1_0",)),
            ("DellRaidService", ("1_5_1",)),
            ("DellRollupStatus", ("1_0_0",)),
            ("DellSecureBoot", ("1_1_0",)),
            ("DellSensor", ("1_0_0",)),
            ("DellServiceRoot", ("1_0_0",)),
            ("DellSlot", ("1_0_0",)),
            ("DellSoftwareInstallationService", ("1_1_2",)),
            ("DellSoftwareInventory", ("1_2_0",)),
            ("DellSwitchConnection", ("1_1_0",)),
            ("DellSystem", ("1_3_0",)),
            ("DellSystemQuickSync", ("1_0_0",)),
            ("DellTelemetryService", ("1_2_0",)),
            ("DellVideo", ("1_2_0",)),
            ("DellVirtualDisk", ("1_2_0",)),
            ("DelliDRACCard", ("1_1_0",)),
            ("DelliDRACCardService", ("1_6_0",)),
            ("Event", ("1_7_1",)),
            ("EventDestination", ("1_12_0",)),
            ("IOStatistics", ("1_0_4",)),
            ("IPAddresses", ("1_1_3",)),
            ("ManagerAccount", ("1_9_0",)),
            ("Message", ("1_1_2",)),
            ("PCIeDevice", ("1_9_0",)),
            ("Redundancy", ("1_4_1",)),
            ("Resource", ("1_14_1",)),
            ("Schedule", ("1_2_2",)),
            ("Sensor", ("1_5_0",)),
            ("Signature", ("1_0_2",)),
            ("SoftwareInventory", ("1_7_0",)),
            ("Storage", ("1_13_0", "1_10_1")),
            ("StorageReplicaInfo", ("1_3_0", "1_4_0")),
            ("VLanNetworkInterface", ("1_3_0",)),
            ("Volume", ("1_6_2",)),
        ]
    )

    def parsed(self, ctx: aiopenapi3.plugin.Document.Context) -> aiopenapi3.plugin.Document.Context:
        super().parsed(ctx)
        self.removeInvalidVersions(ctx, self.VERSIONS)
        self.fixDellManager(ctx)
        self.fixResourceHealth(ctx)
        self.fixTaskService(ctx)
        return ctx


class Document_v7_00_60_00(_DocumentBase):
    VERSIONS = dict(
        [
            ("AccountService", ("1_13_0",)),
            ("Capacity", ("1_2_1",)),
            ("Certificate", ("1_7_0",)),
            ("Circuit", ("1_7_0",)),
            ("ComputerSystem", ("1_20_1",)),
            ("Control", ("1_3_0",)),
            ("DataProtectionLoSCapabilities", ("1_2_0",)),
            ("DataStorageLoSCapabilities", ("1_2_2",)),
            ("DellAssembly", ("1_0_0",)),
            ("DellBIOSService", ("1_0_0",)),
            ("DellChassis", ("1_0_0",)),
            ("DellComputerSystem", ("1_2_0",)),
            ("DellController", ("1_4_1",)),
            ("DellControllerBattery", ("1_0_0",)),
            ("DellDrive", ("1_1_0",)),
            ("DellEnclosure", ("1_1_0",)),
            ("DellEnclosureEMM", ("1_1_0",)),
            ("DellEnclosureFanSensor", ("1_1_0",)),
            ("DellEnclosurePowerSupply", ("1_0_0",)),
            ("DellEnclosureTemperatureSensor", ("1_1_0",)),
            ("DellFC", ("1_4_0",)),
            ("DellFCCapabilities", ("1_0_0",)),
            ("DellFCPortMetrics", ("1_1_1",)),
            ("DellFCStatistics", ("1_0_0",)),
            ("DellFRUAssembly", ("1_1_0",)),
            ("DellFan", ("1_0_0",)),
            ("DellGPUSensor", ("1_1_0",)),
            ("DellInfiniBand", ("1_2_0",)),
            ("DellInfiniBandCapabilities", ("1_0_0",)),
            ("DellInfiniBandPortMetrics", ("1_0_0",)),
            ("DellJobService", ("1_2_0",)),
            ("DellLCService", ("1_6_0",)),
            ("DellLicensableDevice", ("1_0_0",)),
            ("DellLicense", ("1_2_0",)),
            ("DellLicenseManagementService", ("1_1_0",)),
            ("DellLogEntry", ("1_1_0",)),
            ("DellManager", ("1_4_0",)),
            ("DellManagerAccount", ("1_0_0",)),
            ("DellManagerNetworkProtocol", ("1_0_0",)),
            ("DellMemory", ("1_1_0",)),
            ("DellMetricReport", ("1_0_0",)),
            ("DellMetricReportDefinition", ("1_1_0",)),
            ("DellMetricService", ("1_2_0",)),
            ("DellNIC", ("1_6_0",)),
            ("DellNICCapabilities", ("1_2_0",)),
            ("DellNICPortMetrics", ("1_1_1",)),
            ("DellNetworkTransceiver", ("1_1_0",)),
            ("DellNetworkTransceiverPortMetrics", ("1_0_0",)),
            ("DellNumericSensor", ("1_1_1",)),
            ("DellOSDeploymentService", ("1_1_0",)),
            ("DellOem", ("1_3_0",)),
            ("DellOemEnclosureChassis", ("1_0_0",)),
            ("DellOemStorageController", ("1_0_0",)),
            ("DellPCIeFunction", ("1_5_0",)),
            ("DellPCIeSSD", ("1_8_0",)),
            ("DellPCIeSSDExtender", ("1_0_0",)),
            ("DellPSNumericSensor", ("1_1_0",)),
            ("DellPersistentStorageService", ("1_1_0",)),
            ("DellPhysicalDisk", ("1_7_0",)),
            ("DellPowerSupply", ("1_1_1",)),
            ("DellPowerSupplyView", ("1_3_0",)),
            ("DellPresenceAndStatusSensor", ("1_1_0",)),
            ("DellProcessor", ("1_2_0",)),
            ("DellRaidService", ("1_5_1",)),
            ("DellRollupStatus", ("1_0_0",)),
            ("DellSecureBoot", ("1_1_0",)),
            ("DellSensor", ("1_0_0",)),
            ("DellServiceRoot", ("1_0_0",)),
            ("DellSlot", ("1_0_0",)),
            ("DellSoftwareInstallationService", ("1_2_0",)),
            ("DellSoftwareInventory", ("1_2_0",)),
            ("DellSwitchConnection", ("1_1_0",)),
            ("DellSystem", ("1_4_0",)),
            ("DellSystemQuickSync", ("1_0_0",)),
            ("DellTelemetryService", ("1_2_0",)),
            ("DellVideo", ("1_2_0",)),
            ("DellVirtualDisk", ("1_2_0",)),
            ("DelliDRACCard", ("1_1_0",)),
            ("DelliDRACCardService", ("1_7_0",)),
            ("Event", ("1_8_0",)),
            ("EventDestination", ("1_13_1",)),
            ("IPAddresses", ("1_1_3",)),
            ("ManagerAccount", ("1_10_0",)),
            ("Message", ("1_1_2",)),
            ("PCIeDevice", ("1_11_1",)),
            ("Redundancy", ("1_4_1",)),
            ("Resource", ("1_16_0",)),
            ("Schedule", ("1_2_4",)),
            ("Sensor", ("1_7_0",)),
            ("Signature", ("1_0_2",)),
            ("SoftwareInventory", ("1_9_0",)),
            ("Storage", ("1_15_0", "1_10_1")),
            ("StorageReplicaInfo", ("1_3_0", "1_4_0")),
            ("VLanNetworkInterface", ("1_3_0",)),
            ("Volume", ("1_9_0",)),
        ]
    )

    def parsed(self, ctx: aiopenapi3.plugin.Document.Context) -> aiopenapi3.plugin.Document.Context:
        super().parsed(ctx)

        self.removeInvalidVersions(ctx, self.VERSIONS)

        self.fixDellManager(ctx)
        self.fixResourceHealth(ctx)
        self.fixTaskService(ctx)
        return ctx


from pathlib import Path
from aiopenapi3.json import JSONReference


class Document_vX(_DocumentBase):
    """
    Generate Version anyOf …
    """

    def __init__(self, url, directory):
        super().__init__(url)
        self.dir = directory

    def removeInvalidVersions(self, ctx: aiopenapi3.plugin.Document.Context):
        r = collections.defaultdict(lambda: list())
        for name, value in ctx.document["components"]["schemas"].items():
            if "anyOf" not in value:
                continue

            def fileExists(x):
                return (self.dir / "OpenAPI" / Path(JSONReference.split(x["$ref"])[0]).name).exists()

            new = list(filter(fileExists, value["anyOf"]))

            # if (a:=set(JSONReference.split(i["$ref"])[0] for i in new)) != (b:=set(JSONReference.split(i["$ref"])[0] for i in value["anyOf"])):
            #    print(f"{ctx.url}#{name} ({sorted(b - a)})")
            #            if (a := set(JSONReference.split(i["$ref"])[0] for i in new)) != (b := set(JSONReference.split(i["$ref"])[0] for i in value["anyOf"])):
            #                print(f"{ctx.url}#{name} {sorted(a)}")

            for i in new:
                name, _, version = (Path(JSONReference.split(i["$ref"])[0])).stem.partition(".v")
                if name == "odata-v4":
                    continue
                if version not in r[name]:
                    r[name].append(version)

            value["anyOf"] = new

        for name, versions in sorted(r.items(), key=lambda x: x[0]):
            n = tuple([name, tuple(versions)])
            print(n)

    def parsed(self, ctx: aiopenapi3.plugin.Document.Context) -> aiopenapi3.plugin.Document.Context:
        super().parsed(ctx)
        if ctx.url != self._url:
            path = Path(ctx.url.path)
            if "." not in path.stem:
                self.removeInvalidVersions(ctx)

        self.fixDellManager(ctx)
        self.fixResourceHealth(ctx)
        self.fixTaskService(ctx)
        return ctx


def Received(*patterns, method=None):
    return _Routes("_received", *patterns, method=method)


def Parsed(*patterns, method=None):
    return _Routes("_parsed", *patterns, method=method)


def _Routes(_route, *patterns, method=None):
    def x(f):
        setattr(f, _route, (m := getattr(f, _route, set())))
        m.update(frozenset((p, tuple(method) if method else None) for p in patterns))
        return f

    return x


class Message(aiopenapi3.plugin.Message):
    class Methods:
        def __init__(self):
            self._get = self._post = self._patch = self._put = self._delete = None
            self.default = None

        @property
        def get(self):
            return self._get or self.default

        @property
        def post(self):
            return self._post or self.default

        @property
        def patch(self):
            return self._patch or self.default

        @property
        def put(self):
            return self._put or self.default

        @property
        def delete(self):
            return self._delete or self.default

    def __init__(self):
        super().__init__()
        self._received = collections.defaultdict(lambda: Message.Methods())
        self._parsed = collections.defaultdict(lambda: Message.Methods())
        for op, mapping in {"_received": self._received, "_parsed": self._parsed}.items():
            for name, i in filter(
                lambda kv: kv[1] and inspect.ismethod(kv[1]) and hasattr(kv[1], op),
                map(lambda x: (x, getattr(self, x)), dir(self)),
            ):
                objmap = getattr(i, op)
                for url, methods in objmap:
                    if methods:
                        for m in methods:
                            setattr(mapping[url], f"_{m}", i)
                    else:
                        mapping[url].default = i

    def _dr(self, what, ctx):
        if (r := what.get(ctx.request.path, None)) and (m := getattr(r, ctx.request.method, None)):
            m(ctx)
        return ctx

    def parsed(self, ctx: "aiopenapi3.plugin.Message.Context") -> "aiopenapi3.plugin.Message.Context":
        return self._dr(self._parsed, ctx)

    def received(self, ctx: "aiopenapi3.plugin.Message.Context") -> "aiopenapi3.plugin.Message.Context":
        """
        7.5 Data modification requests

        status_code 202 data modification requests do not return a Task as required by the spec but only a url to the
        Task in the Location header
        As the plugin interface is not async, we can not retrieve the actual Task and are limited create a Task limited
        to the TaskId to work with
        """
        match ctx.request.method, ctx.status_code:
            case ["post" | "put" | "patch", "202"]:
                """
                DSP0266 - 7.5.2 Modification success responses
                """
                location = ctx.headers["Location"]
                _, _, jobid = location.rpartition("/")
                ctx.received = json.dumps(
                    {
                        "@odata.id": location,
                        "@odata.type": "#Task._.Task",
                        "Id": jobid,
                        "Name": "",
                    }
                )
        return self._dr(self._received, ctx)

    @Parsed("/redfish/v1/Managers/{ManagerId}/Oem/Dell/DellAttributes/{DellAttributesId}", method=["patch"])
    @Parsed("/redfish/v1/AccountService/Accounts/{ManagerAccountId}", method=["patch", "post"])
    @Parsed("/redfish/v1/SessionService/Sessions/{SessionId}", method=["delete"])
    def dr_NODATA(self, ctx: "Message.Context"):
        """
        The response to a modification request is empty and only carries a Success Message
        As the modified response object is missing from the response, validation will fail
        Forge a response which consists of the model modified and the changes to pass validation
        """

        if not ((context := ctx.request.vars.context) and isinstance(context._v, ctx.expected_type.get_type())):
            return ctx
        assert ctx.request.method in ["post", "patch", "delete"]

        if (
            len(ctx.parsed.keys()) == 1
            and (v := ctx.parsed.get("@Message.ExtendedInfo", None)) is not None
            and any(map(lambda x: x["MessageId"] == "Base.1.12.Success", v))
        ):
            data = context._v.model_dump(by_alias=True, exclude_unset=True)
            data.update(ctx.parsed)
            if ctx.request.vars.data is not None:
                data.update(ctx.request.vars.data)
            ctx.parsed = data
        else:
            pass

    @Parsed("/redfish/v1/TaskService/Tasks/{TaskId}", method=["get"])
    def dr_Task_MessageId(self, ctx: "Message.Context") -> "Message.Context":
        for i in ctx.parsed.get("Messages", []):
            if "MessageId" not in i:
                i["MessageId"] = ""
        return ctx

    @Parsed("/redfish/v1/Systems/{ComputerSystemId}")
    def dr_LastResetTime(self, ctx: "Message"):
        if (
            "LastResetTime" in ctx.expected_type.get_type().model_fields
            and ctx.parsed.get("LastResetTime", None) == "0000-00-00T00:00:00+00:00"
        ):
            # '0000-00-00T00:00:00+00:00'
            del ctx.parsed["LastResetTime"]
        return ctx


from aiopenapi3_redfish.entities.service import AsyncTaskService
from typing import Union
from aiopenapi3_redfish.oem import Detour


@Detour("/redfish/v1/TaskService")
@Detour("#TaskService..TaskService")
@Detour("#ServiceRoot..ServiceRoot/Tasks")
class DellTaskServiceMonitor(AsyncTaskService):
    async def wait_for(
        self, TaskId: str, pollInterval: int = 7, maxWait: int = 700
    ) -> Union[AsyncTaskService.AsyncTask, bytes]:
        """
        Dell TaskService combines the functionality with the TaskMonitor and may return result data instead of Tasks
        we modified the description document in fixTaskService() to accept response content types other than
        application/json.
        Therefore .index() can return non Task objects: bytes.
        """
        try:
            return await super().wait_for(TaskId, pollInterval, maxWait)
        except TypeError as e:
            return e.args[0]
