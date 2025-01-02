import io
import copy
from pathlib import Path

import yaml
import yarl

import aiopenapi3.plugin


class _DocumentBase(aiopenapi3.plugin.Document):
    def __init__(self, url):
        self._url = url
        super().__init__()

    def parsed(self, ctx: aiopenapi3.plugin.Document.Context) -> aiopenapi3.plugin.Document.Context:
        if str(ctx.url) == self._url:
            # mangle the Task refs in the loaded openapi.yaml
            for k, v in ctx.document["paths"].items():
                for o, op in v.items():
                    if o not in aiopenapi3.base.HTTP_METHODS:
                        continue
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
                    if o not in aiopenapi3.base.HTTP_METHODS:
                        continue
                    if "security" not in op:
                        continue
                    if op["security"] == [{"basicAuth": [], "X-Auth": []}]:
                        op["security"] = [{"basicAuth": []}, {"X-Auth": []}]

            data = ctx.document
            """
            DellAttributes Alias
            /redfish/v1/Managers/{ManagerId}/Attributes -> /redfish/v1/Managers/{ManagerId}/Oem/Dell/DellAttributes/{DellAttributesId}
            """
            if (
                "/redfish/v1/Managers/{ManagerId}/Oem/Dell/DellAttributes/{DellAttributesId}" in data["paths"]
                and "/redfish/v1/Managers/{ManagerId}/Attributes" not in data["paths"]
            ):
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
