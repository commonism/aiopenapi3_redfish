import typing
import re

import aiopenapi3.plugin

import aiopenapi3_redfish.clinic
from aiopenapi3_redfish.clinic import Parsed
from aiopenapi3_redfish.entities.service import AsyncTaskService
from aiopenapi3_redfish.oem import Detour

if typing.TYPE_CHECKING:
    pass

from .base import Document_vX
from .version import *


class Message(aiopenapi3_redfish.clinic.Message):
    @Parsed("/redfish/v1/Systems/{ComputerSystemId}", method=["patch"])
    @Parsed("/redfish/v1/Managers/{ManagerId}/Oem/Dell/DellAttributes/{DellAttributesId}", method=["patch"])
    @Parsed("/redfish/v1/AccountService/Accounts/{ManagerAccountId}", method=["patch", "post"])
    @Parsed("/redfish/v1/SessionService/Sessions/{SessionId}", method=["delete"])
    def dr_NODATA(self, ctx: "aiopenapi3.plugin.Message.Context"):
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
            and any(map(lambda x: re.match(r"Base.\d+.\d+.Success", x["MessageId"]), v))
        ):
            data = context._v.model_dump(by_alias=True, exclude_unset=True)
            data.update(ctx.parsed)
            if ctx.request.vars.data is not None:
                data.update(ctx.request.vars.data)
            ctx.parsed = data
        else:
            pass

    @Parsed("/redfish/v1/TaskService/Tasks/{TaskId}", method=["get"])
    def dr_Task_MessageId(self, ctx: "aiopenapi3.plugin.Message.Context") -> "aiopenapi3.plugin.Message.Context":
        # 1.10.17.00
        if ctx.parsed.get("Name") is None:
            ctx.parsed["Name"] = ""

        if "MessageArgs@AUTO_COUNT" in ctx.parsed.get("Oem", {}).get("Dell", {}):
            del ctx.parsed["Oem"]["Dell"]["MessageArgs@AUTO_COUNT"]

        for i in ctx.parsed.get("Messages", []):
            if "MessageID" in i:  # v7.20.10.05
                i["MessageId"] = i["MessageID"]
                del i["MessageID"]
            if "MessageId" not in i:
                i["MessageId"] = ""

        return ctx

    @Parsed("/redfish/v1/Systems/{ComputerSystemId}")
    def dr_LastResetTime(self, ctx: "aiopenapi3.plugin.Message.Context") -> "aiopenapi3.plugin.Message.Context":
        if (
            "LastResetTime" in ctx.expected_type.get_type().model_fields
            and ctx.parsed.get("LastResetTime", None) == "0000-00-00T00:00:00+00:00"
        ):
            # '0000-00-00T00:00:00+00:00'
            del ctx.parsed["LastResetTime"]
        return ctx

    @Parsed("/redfish/v1/Managers/{ManagerId}")
    def dr_Manager(self, ctx: "aiopenapi3.plugin.Message.Context") -> "aiopenapi3.plugin.Message.Context":
        if ctx.request.vars.parameters["ManagerId"] == "iDRAC.Embedded.1":
            """iDRAC v4.32.10.00"""
            if item := ctx.parsed.get("Oem", {}).get("Dell", {}).get("DelliDRACCard", {}):
                for k, v in {"Id": "0", "Name": "yes"}.items():
                    if k not in item:
                        item[k] = v

            t = "#DellOem.v1_3_0.DellOemLinks"
            if (w := ctx.parsed.get("Links", {}).get("Oem").get("Dell", {})).get("@odata.type", "") != t:
                w["@odata.type"] = t

            """v7.20.10.05"""
            if "ServiceIdentification" in ctx.parsed:
                del ctx.parsed["ServiceIdentification"]

        return ctx

    @Parsed("/redfish/v1/Systems/{ComputerSystemId}/Storage/{StorageId}/Drives/{DriveId}")
    @Parsed("/redfish/v1/Systems/{ComputerSystemId}/Storage/{StorageId}/Volumes/{VolumeId}")
    @Parsed("/redfish/v1/Systems/{ComputerSystemId}/Storage/{StorageId}")
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

    @Parsed("/redfish/v1/Managers/{ManagerId}/Oem/Dell/Jobs/{DellJobId}")
    def dr_DellJob(self, ctx: "aiopenapi3.plugin.Message.Context") -> "aiopenapi3.plugin.Message.Context":
        for i in ["ActualRunningStopTime", "ActualRunningStartTime"]:
            if not isinstance(ctx.parsed[i], str):
                ctx.parsed[i] = str(ctx.parsed[i])
        return ctx

    @Parsed(
        "/redfish/v1/Managers/{ManagerId}/Oem/Dell/DelliDRACCardService/Actions/DelliDRACCardService.ImportCertificate",
        method=["post"],
    )
    def dr_ImportCertificate(self, ctx: "aiopenapi3.plugin.Message.Context") -> "aiopenapi3.plugin.Message.Context":
        if "error" not in ctx.parsed:
            p = {"error": {"code": "-", "message": "-", "@Message.ExtendedInfo": ctx.parsed["@Message.ExtendedInfo"]}}
            ctx.parsed = p
        return ctx


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
