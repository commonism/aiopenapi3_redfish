import inspect
from pathlib import Path
import copy
import json
import collections

import yarl

import aiopenapi3
import aiopenapi3.plugin


class Document(aiopenapi3.plugin.Document):
    def __init__(self, url):
        self._url = url
        super().__init__()

    def parsed(self, ctx):
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
            import yaml
            import io

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

            # inject DellOem in components to use
            ctx.document["components"]["schemas"]["DellOem_DellOemLinks"] = {
                "$ref": "/redfish/v1/Schemas/DellOem.v1_3_0.yaml#/components/schemas/DellOem_v1_3_0_DellOemLinks"
            }

        if ctx.url.path == "/redfish/v1/Schemas/DellOem.v1_3_0.yaml":
            pass

        if ctx.url.path == "/redfish/v1/Schemas/Resource.yaml":
            for name, value in ctx.document["components"]["schemas"].items():
                if "anyOf" not in value:
                    continue

                #                breakpoint()
                def filtersensors(x):
                    u = yarl.URL(x["$ref"])
                    return Path(u.path).name.partition(".")[0] == "Resource" and Path(u.path).name not in [
                        "Resource.v1_0_0.yaml",
                        "Resource.v1_14_1.yaml",
                    ]

                l = [i for i in value["anyOf"] if i not in list(filter(filtersensors, value["anyOf"]))]
                value["anyOf"] = l
            return ctx

        for name in [
            "Capacity.v1_2_0.yaml",
            "Control.v1_1_0.yaml",
            "DellFRUAssembly.v1_1_0.yaml",
            "DellManager.v1_3_0.yaml",
            "DellTelemetryService.v1_2_0.yaml",
            "DellMetricReportDefinition.v1_1_0.yaml",
            "DellSecureBoot.v1_1_0.yaml",
            "IPAddresses.v1_1_3.yaml",
            "Message.v1_1_2.yaml",
            "PCIeDevice.v1_9_0.yaml",
            "Schedule.v1_2_2.yaml",
            "SoftwareInventory.v1_7_0.yaml",
            "StorageReplicaInfo.v1_4_0.yaml",  # StorageReplicaInfo.v1_3_0.yaml
            "VLanNetworkInterface.v1_3_0.yaml",
            "Sensor.v1_5_0.yaml",
        ]:
            root, version, _ = name.split(".")
            if ctx.url.path == f"/redfish/v1/Schemas/{root}.yaml":
                for name, value in ctx.document["components"]["schemas"].items():
                    if "anyOf" not in value:
                        continue

                    def filtersensors(x):
                        u = yarl.URL(x["$ref"])
                        return (
                            Path(u.path).name.partition(".")[0] == root
                            and u.path != f"/redfish/v1/Schemas/{root}.{version}.yaml"
                        )

                    l = [i for i in value["anyOf"] if i not in list(filter(filtersensors, value["anyOf"]))]
                    value["anyOf"] = l
                return ctx

        if ctx.url.path == "/redfish/v1/Schemas/DellManager.v1_3_0.yaml":
            """
            DelliDRACCard correction …
            """
            if "DellManager_v1_3_0_DellManager" in ctx.document["components"]["schemas"]:
                v = ctx.document["components"]["schemas"]["DellManager_v1_3_0_DellManager"]["properties"]

                # Fix DelliDRACCard $ref
                assert (
                    v["DelliDRACCard"]["$ref"] == "/redfish/v1/Schemas/odata-v4.yaml#/components/schemas/odata-v4_idRef"
                )
                v["DelliDRACCard"] = {
                    "$ref": "/redfish/v1/Schemas/DelliDRACCard.yaml#/components/schemas/DelliDRACCard_DelliDRACCard"
                }

        return ctx


def Received(*patterns, method=None):
    return Routes("_received", *patterns, method=method)


def Parsed(*patterns, method=None):
    return Routes("_parsed", *patterns, method=method)


def Routes(_route, *patterns, method=None):
    def x(f):
        p = _route
        setattr(f, p, (m := getattr(f, p, set())))
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
        return None

    def _dr(self, what, ctx):
        if (r := what.get(ctx.request.path, None)) and (m := getattr(r, ctx.request.method, None)):
            m(ctx)
        return ctx

    def parsed(self, ctx: "Message.Context") -> "Message.Context":
        return self._dr(self._parsed, ctx)

    def received(self, ctx: "Message.Context") -> "Message.Context":
        return self._dr(self._received, ctx)

    @Parsed("/redfish/v1/AccountService/Accounts/{ManagerAccountId}", method=["patch", "post"])
    @Parsed("/redfish/v1/SessionService/Sessions/{SessionId}", method=["delete"])
    def dr_NODATA(self, ctx: "Message.Context"):
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

    @Received("/redfish/v1/TaskService/Tasks/{TaskId}", method=["get"])
    def dr_Task(self, ctx: "Message.Context") -> "Message.Context":
        if ctx.status_code != "200":
            ctx.status_code = "200"
        else:
            if ctx.content_type.partition(";")[0].lower() != "application/json":
                ctx.received = json.dumps(
                    {
                        "@odata.id": ctx.request.req.url,
                        "@odata.type": "#Task._.Task",
                        "Id": ctx.request.vars.parameters["TaskId"],
                        "Name": "",
                        "Messages": [{"MessageId": "", "Message": ctx.received.decode("utf-8")}],
                    }
                )
                ctx.content_type = "application/json"
        return ctx

    @Received("/redfish/v1/Managers/{ManagerId}/Actions/Oem/EID_674_Manager.ExportSystemConfiguration", method=["post"])
    def dr_ExportSystemConfiguration(self, ctx: "Message.Context") -> "Message.Context":
        location = ctx.headers["Location"]
        _, _, jobid = location.rpartition("/")
        ctx.received = json.dumps(
            {
                "@odata.id": location,
                "@odata.type": "#Task._.Task",
                "Id": jobid,
                "Name": "Export: Server Configuration Profile",
            }
        )
        return ctx
