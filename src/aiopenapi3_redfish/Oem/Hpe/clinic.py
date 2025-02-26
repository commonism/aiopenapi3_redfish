import typing

import aiopenapi3.plugin

import aiopenapi3_redfish.clinic
from aiopenapi3_redfish.clinic import Parsed
from aiopenapi3_redfish.entities.service import AsyncTaskService
from aiopenapi3_redfish.oem import Detour

if typing.TYPE_CHECKING:
    pass


class NoOemMessage(aiopenapi3.plugin.Message):
    """
    Hpe choose not to provide description documents for iLO

    https://github.com/HewlettPackard/python-ilorest-library/issues/158
    """

    def parsed(self, ctx: "aiopenapi3.plugin.Message.Context") -> "aiopenapi3.plugin.Message.Context":
        if (oem := ctx.parsed.get("Oem", {})) and oem.get("Hpe"):
            del oem["Hpe"]
        return ctx


class Message(aiopenapi3_redfish.clinic.Message):
    @Parsed("/redfish/v1/Chassis/{ChassisId}/NetworkAdapters/{NetworkAdapterId}", method=["get"])
    def dr_NetworkAdapter(self, ctx: "aiopenapi3.plugin.Message.Context"):
        if "Actions" in ctx.parsed:
            del ctx.parsed["Actions"]
        return ctx

    @Parsed("/redfish/v1/Chassis/{ChassisId}/NetworkAdapters/{NetworkAdapterId}/Ports/{PortId}", method=["get"])
    def dr_Port(self, ctx: "aiopenapi3.plugin.Message.Context"):
        if "Actions" in ctx.parsed:
            del ctx.parsed["Actions"]
        if "@Redfish.Settings" in ctx.parsed:
            del ctx.parsed["@Redfish.Settings"]
        for i in ["LLDPReceive", "LLDPTransmit"]:
            del ctx.parsed["Ethernet"][i]
        return ctx
