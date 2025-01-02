import typing
import yarl

import yaml

import aiopenapi3.plugin

import aiopenapi3_redfish.clinic

if typing.TYPE_CHECKING:
    pass

from .documents.v6_10_00_00 import Document_v6_10_00_00
from .documents.v7_00_60_00 import Document_v7_00_60_00
from .documents.v7_10_30_00 import Document_v7_10_30_00
from .documents.v7_10_75_00 import Document_v7_10_75_00
from .documents.generator import Document_vX


class Message(aiopenapi3_redfish.clinic.Message):
    @aiopenapi3_redfish.clinic.Parsed("/redfish/v1/Systems/{ComputerSystemId}", method=["patch"])
    @aiopenapi3_redfish.clinic.Parsed(
        "/redfish/v1/Managers/{ManagerId}/Oem/Dell/DellAttributes/{DellAttributesId}", method=["patch"]
    )
    @aiopenapi3_redfish.clinic.Parsed(
        "/redfish/v1/AccountService/Accounts/{ManagerAccountId}", method=["patch", "post"]
    )
    @aiopenapi3_redfish.clinic.Parsed("/redfish/v1/SessionService/Sessions/{SessionId}", method=["delete"])
    def dr_NODATA(self, ctx: "aiopenapi3.plugin.Message.Context"):
        """
        The response to a modification request is empty and only carries a Success Message
        As the modified response object is missing from the response, validation will fail
        Forge a response which consists of the model modified and the changes to pass validation
        """

        if not ((context := ctx.request.vars.context) and isinstance(context._v, ctx.expected_type.get_type())):
            return ctx
        assert ctx.request.method in ["post", "patch", "delete"]

        import re

        if (
            len(ctx.parsed.keys()) == 1
            and (v := ctx.parsed.get("@Message.ExtendedInfo", None)) is not None
            and any(map(lambda x: re.match(r"Base.\d+.\d+.Success", x["MessageId"]), v))
        ):
            data = context._v.model_dump(by_alias=True, exclude_unset=True)
            data.update(ctx.parsed)
            if ctx.request.vars.data is not None:
                data.update(ctx.request.vars.data)
            ctx.parsed = data
        else:
            pass

    @aiopenapi3_redfish.clinic.Parsed("/redfish/v1/TaskService/Tasks/{TaskId}", method=["get"])
    def dr_Task_MessageId(self, ctx: "aiopenapi3.plugin.Message.Context") -> "aiopenapi3.plugin.Message.Context":
        for i in ctx.parsed.get("Messages", []):
            if "MessageId" not in i:
                i["MessageId"] = ""
        return ctx

    @aiopenapi3_redfish.clinic.Parsed("/redfish/v1/Systems/{ComputerSystemId}")
    def dr_LastResetTime(self, ctx: "aiopenapi3.plugin.Message.Context") -> "aiopenapi3.plugin.Message.Context":
        if (
            "LastResetTime" in ctx.expected_type.get_type().model_fields
            and ctx.parsed.get("LastResetTime", None) == "0000-00-00T00:00:00+00:00"
        ):
            # '0000-00-00T00:00:00+00:00'
            del ctx.parsed["LastResetTime"]
        return ctx

    @aiopenapi3_redfish.clinic.Parsed("/redfish/v1/Managers/{ManagerId}")
    def dr_Manager(self, ctx: "aiopenapi3.plugin.Message.Context") -> "aiopenapi3.plugin.Message.Context":
        """iDRAC v4.32.10.00"""
        if ctx.request.vars.parameters["ManagerId"] == "iDRAC.Embedded.1":
            if item := ctx.parsed.get("Oem", {}).get("Dell", {}).get("DelliDRACCard", {}):
                for k, v in {"Id": "0", "Name": "yes"}.items():
                    if k not in item:
                        item[k] = v

            t = "#DellOem.v1_3_0.DellOemLinks"
            if (w := ctx.parsed.get("Links", {}).get("Oem").get("Dell", {})).get("@odata.type", "") != t:
                w["@odata.type"] = t

        return ctx

    @aiopenapi3_redfish.clinic.Parsed("/redfish/v1/Systems/{ComputerSystemId}/Storage/{StorageId}/Drives/{DriveId}")
    @aiopenapi3_redfish.clinic.Parsed("/redfish/v1/Systems/{ComputerSystemId}/Storage/{StorageId}/Volumes/{VolumeId}")
    @aiopenapi3_redfish.clinic.Parsed("/redfish/v1/Systems/{ComputerSystemId}/Storage/{StorageId}")
    def dr_AllowableValues(self, ctx: "aiopenapi3.plugin.Message.Context") -> "aiopenapi3.plugin.Message.Context":
        # remove @Redfish.____@Redfish.AllowableValues
        # @ is not a valid character for properties
        actions = list((k, v) for k, v in ctx.parsed.get("Actions", {}).items() if k[0] == "#")
        actions.extend(list((k, v) for k, v in ctx.parsed.get("Actions", {}).get("Oem", {}).items() if k[0] == "#"))

        for k, v in actions:
            for kk in list(v.keys()):
                if kk.startswith("@Redfish.") and kk.count("@") > 1:
                    del v[kk]
        return ctx


from aiopenapi3_redfish.entities.service import AsyncTaskService
from aiopenapi3_redfish.oem import Detour


@Detour("/redfish/v1/TaskService")
@Detour("#TaskService..TaskService")
@Detour("#ServiceRoot..ServiceRoot/Tasks")
class DellTaskServiceMonitor(AsyncTaskService):
    async def wait_for(
        self, TaskId: str, pollInterval: int = 7, maxWait: int = 700
    ) -> AsyncTaskService.AsyncTask | bytes:
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
