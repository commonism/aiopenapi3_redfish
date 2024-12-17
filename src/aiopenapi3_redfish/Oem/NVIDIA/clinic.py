import typing
import json
import aiopenapi3_redfish.clinic

if typing.TYPE_CHECKING:
    import aiopenapi3.plugin


class Message(aiopenapi3_redfish.clinic.Message):
    @aiopenapi3_redfish.clinic.Parsed("/redfish/v1/AccountService/Accounts/{ManagerAccountId}", method=["get"])
    def dr_ManagerAccount(self, ctx: "aiopenapi3.plugin.Message.Context"):
        ctx.parsed["AccountTypes"] = []
        return ctx

    @aiopenapi3_redfish.clinic.Parsed("/redfish/v1/TelemetryService", method=["get"])
    def dr_TelemetryService(self, ctx: "aiopenapi3.plugin.Message.Context"):
        ctx.parsed["SupportedCollectionFunctions"] = list(
            set(ctx.parsed["SupportedCollectionFunctions"])
            & set(ctx.parsed["SupportedCollectionFunctions@Redfish.AllowableValues"])
        )
        return ctx

    @aiopenapi3_redfish.clinic.Received(
        "/redfish/v1/Systems/{ComputerSystemId}/Actions/ComputerSystem.Reset", method=["post"]
    )
    def dr_Reset(self, ctx: "aiopenapi3.plugin.Message.Context"):
        parsed = json.loads(ctx.received)
        if not isinstance(parsed, dict):
            return

        if ctx.status_code == "200" and len(frozenset(parsed.keys()) & frozenset(["code", "error"])) != 2:
            # should be a Task instead
            if isinstance(parsed.get("@Message.ExtendedInfo", None), list):
                ctx.status_code = "202"
                t = {
                    "@odata.id": "Task",
                    "@odata.type": "Task._.Task",
                    "Id": "",
                    "Name": "Reset",
                    "Messages": parsed["@Message.ExtendedInfo"],
                }
            else:
                raise ValueError("unexpected format")
            ctx.received = json.dumps(t)

    @aiopenapi3_redfish.clinic.Parsed("/redfish/v1/Chassis/{ChassisId}", method=["get"])
    def dr_Chassis(self, ctx: "aiopenapi3.plugin.Message.Context"):
        if ctx.parsed.get("ChassisType", "") == "Rack Mount Chassis":
            ctx.parsed["ChassisType"] = "Rack"
        if (v := "ProductName") in ctx.parsed:
            del ctx.parsed[v]
