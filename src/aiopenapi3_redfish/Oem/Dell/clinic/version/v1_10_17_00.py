import typing
import io

import yaml

import aiopenapi3.plugin

from ..base import _DocumentBase

if typing.TYPE_CHECKING:
    pass


class Document_v1_10_17_00(_DocumentBase):
    VERSIONS = dict()  # ! yay

    def fixServiceRoot(self, ctx: aiopenapi3.plugin.Document.Context):
        if ctx.url.path.endswith("ServiceRoot.v1_17_0.yaml"):
            # iDRAC 1_10_17_00 lacks the telemetry service
            ctx.document["components"]["schemas"]["ServiceRoot_v1_17_0_ServiceRoot"]["properties"][
                "TelemetryService"
            ] = yaml.safe_load(
                io.StringIO(
                    """
                  $ref: /redfish/v1/Schemas/odata-v4.yaml#/components/schemas/odata-v4_idRef
                  description: The link to the telemetry service.
                  readOnly: true
                  x-longDescription: This property shall contain a link to a resource of type
                    `TelemetryService`.
                  x-versionAdded: v1_4_0
                """
                )
            )

    def fixTaskMonitors(self, ctx: aiopenapi3.plugin.Document.Context):
        try:
            ctx.document["paths"]["/redfish/v1/TaskService/TaskMonitors/{TaskMonitorId}"]["get"]["tags"] = ["Task"]
            ctx.document["paths"]["/redfish/v1/TaskService/TaskMonitors/{TaskMonitorId}"]["parameters"] = (
                yaml.safe_load(
                    io.StringIO(
                        """
- name: TaskMonitorId
  schema:
    type: string
  required: true
  in: path
            """
                    )
                )
            )

        except KeyError:
            pass

    def fixOemComputerSystem(self, ctx: aiopenapi3.plugin.Document.Context) -> aiopenapi3.plugin.Document.Context:
        if ctx.url.path.endswith("OemComputerSystem.v1_0_0.yaml"):
            ctx.document["components"]["schemas"]["OemComputerSystem_v1_0_0_ComputerSystem"]["properties"][
                "DellSystem"
            ]["$ref"] = "/redfish/v1/DellSystem.v1_4_0.yaml#/components/schemas/DellSystem_v1_4_0_DellSystem"

    def fixDellChassis(self, ctx: aiopenapi3.plugin.Document.Context) -> aiopenapi3.plugin.Document.Context:
        if ctx.url.path.endswith("Chassis.v1_25_1.yaml"):
            ctx.document["components"]["schemas"]["Chassis_v1_25_1_Chassis_Oem"]["properties"]["Dell"] = {
                "$ref": "/redfish/v1/DellOemChassis.v1_3_0.yaml#/components/schemas/DellOemChassis_v1_3_0_DellOemChassis"
            }

        if ctx.url.path.endswith("DellOemChassis.v1_3_0.yaml"):
            ctx.document["components"]["schemas"]["DellOemChassis_v1_3_0_DellOemChassis"]["properties"][
                "DellChassis"
            ] = {"$ref": "/redfish/v1/DellChassis.v1_0_0.yaml#/components/schemas/DellChassis_v1_0_0_DellChassis"}

    def fixNetworkAdapter(self, ctx: aiopenapi3.plugin.Document.Context) -> aiopenapi3.plugin.Document.Context:
        if ctx.url.path.endswith("NetworkAdapter.v1_11_0.yaml"):
            ctx.document["components"]["schemas"]["NetworkAdapter_v1_11_0_NetworkAdapter"]["properties"]["Oem"] = {
                "$ref": "/redfish/v1/Schemas/Resource.yaml#/components/schemas/Resource_Oem"
            }

    def fixDellNetworkDeviceFunction(self, ctx: aiopenapi3.plugin.Document.Context):
        if ctx.url.path.endswith("DellNetworkDeviceFunction.v1_0_0.yaml"):
            #            ctx.document["components"]["schemas"]["DellNetworkDeviceFunction_v1_0_0_DellNetworkDeviceFunction"]["properties"]\
            #                ["DellNIC"] = {"$ref": "/redfish/v1/DellNIC.v1_7_0.yaml#/components/schemas/DellNIC_v1_7_0_DellNIC"}

            #            ctx.document["components"]["schemas"]["DellNetworkDeviceFunction_v1_0_0_DellNetworkDeviceFunction"]["properties"]\
            #                ["DellNICCapabilities"] = {"$ref": "/redfish/v1/DellNICCapabilities.v1_2_0.yaml#/components/schemas/DellNICCapabilities_v1_2_0_DellNICCapabilities"}

            u = {}
            for k, v in ctx.document["components"]["schemas"][
                "DellNetworkDeviceFunction_v1_0_0_DellNetworkDeviceFunction"
            ]["properties"].items():
                u[k] = {"$ref": f"/redfish/v1/{k}.yaml#/components/schemas/{k}_{k}"}

            for k, v in u.items():
                ctx.document["components"]["schemas"]["DellNetworkDeviceFunction_v1_0_0_DellNetworkDeviceFunction"][
                    "properties"
                ][k].update(v)

    def parsed(self, ctx: aiopenapi3.plugin.Document.Context) -> aiopenapi3.plugin.Document.Context:
        super().parsed(ctx)
        self.fixServiceRoot(ctx)
        self.fixTaskMonitors(ctx)
        self.fixDellManager(ctx)
        self.fixOemComputerSystem(ctx)
        self.fixDellChassis(ctx)
        self.fixNetworkAdapter(ctx)
        self.fixDellNetworkDeviceFunction(ctx)
