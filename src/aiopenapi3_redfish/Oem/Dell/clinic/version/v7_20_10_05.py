import typing
from pathlib import Path
import io

import yaml

import aiopenapi3.plugin

from ..base import _DocumentBase

if typing.TYPE_CHECKING:
    pass


class Document_v7_20_10_05(_DocumentBase):
    VERSIONS = dict(
        [
            ("AccountService", ("1_15_1",)),
            ("ActionInfo", ("1_4_2",)),
            ("Capacity", ("1_2_1",)),
            ("Certificate", ("1_8_2",)),
            ("Circuit", ("1_8_0",)),
            ("ComputerSystem", ("1_22_1",)),
            ("Control", ("1_5_1",)),
            ("DataProtectionLoSCapabilities", ("1_2_0",)),
            ("DataStorageLoSCapabilities", ("1_2_2",)),
            ("DellAssembly", ("1_1_0",)),
            ("DellBIOSService", ("1_0_0",)),
            ("DellChassis", ("1_0_0",)),
            ("DellComputerSystem", ("1_2_0",)),
            ("DellController", ("1_5_0",)),
            ("DellControllerBattery", ("1_0_0",)),
            ("DellDrive", ("1_1_0",)),
            ("DellEnclosure", ("1_1_0",)),
            ("DellEnclosureEMM", ("1_1_0",)),
            ("DellEnclosureFanSensor", ("1_1_0",)),
            ("DellEnclosurePowerSupply", ("1_0_0",)),
            ("DellEnclosureTemperatureSensor", ("1_1_0",)),
            ("DellFan", ("1_0_0",)),
            ("DellFC", ("1_4_0",)),
            ("DellFCCapabilities", ("1_0_0",)),
            ("DellFCPortMetrics", ("1_1_1",)),
            ("DellFCStatistics", ("1_0_0",)),
            ("DellFRUAssembly", ("1_1_0",)),
            ("DellGPUSensor", ("1_2_0",)),
            ("DelliDRACCard", ("1_1_0",)),
            ("DelliDRACCardService", ("1_9_0",)),
            ("DellInfiniBand", ("1_3_0",)),
            ("DellInfiniBandCapabilities", ("1_0_0",)),
            ("DellInfiniBandPortMetrics", ("1_0_0",)),
            ("DellJobService", ("1_2_0",)),
            ("DellLCService", ("1_8_1",)),
            ("DellLicensableDevice", ("1_0_0",)),
            ("DellLicense", ("1_2_0",)),
            ("DellLicenseManagementService", ("1_1_0",)),
            ("DellLogEntry", ("1_1_0",)),
            ("DellManager", ("1_4_0",)),
            ("DellManagerAccount", ("1_0_0",)),
            ("DellManagerNetworkProtocol", ("1_0_1",)),
            ("DellMemory", ("1_1_0",)),
            ("DellMetricReport", ("1_0_0",)),
            ("DellMetricReportDefinition", ("1_1_0",)),
            ("DellMetricService", ("1_2_0",)),
            ("DellNetworkTransceiver", ("1_1_0",)),
            ("DellNetworkTransceiverPortMetrics", ("1_0_0",)),
            ("DellNIC", ("1_7_0",)),
            ("DellNICCapabilities", ("1_2_0",)),
            ("DellNICPortMetrics", ("1_1_1",)),
            ("DellNumericSensor", ("1_1_1",)),
            ("DellOem", ("1_3_0",)),
            ("DellOemEnclosureChassis", ("1_0_0",)),
            ("DellOemStorageController", ("1_0_0",)),
            ("DellOSDeploymentService", ("1_1_0",)),
            ("DellPCIeFunction", ("1_6_0",)),
            ("DellPCIeSSD", ("1_9_0",)),
            ("DellPCIeSSDExtender", ("1_0_0",)),
            ("DellPersistentStorageService", ("1_1_0",)),
            ("DellPhysicalDisk", ("1_7_0",)),
            ("DellPowerSupply", ("1_1_1",)),
            ("DellPowerSupplyView", ("1_3_1",)),
            ("DellPresenceAndStatusSensor", ("1_1_0",)),
            ("DellProcessor", ("1_2_0",)),
            ("DellPSNumericSensor", ("1_1_0",)),
            ("DellRaidService", ("1_5_1",)),
            ("DellRollupStatus", ("1_0_0",)),
            ("DellSecureBoot", ("1_1_0",)),
            ("DellSensor", ("1_0_0",)),
            ("DellServiceRoot", ("1_0_0",)),
            ("DellSlot", ("1_0_0",)),
            ("DellSoftwareInstallationService", ("1_3_1",)),
            ("DellSoftwareInventory", ("1_2_0",)),
            ("DellSwitchConnection", ("1_1_0",)),
            ("DellSystem", ("1_4_0",)),
            ("DellSystemQuickSync", ("1_0_0",)),
            ("DellTelemetryService", ("1_2_0",)),
            ("DellVideo", ("1_3_0",)),
            ("DellVirtualDisk", ("1_2_0",)),
            ("Event", ("1_10_1",)),
            ("EventDestination", ("1_14_1",)),
            ("IPAddresses", ("1_1_5",)),
            ("ManagerAccount", ("1_12_1",)),
            ("Message", ("1_2_1",)),
            ("PCIeDevice", ("1_14_0",)),
            ("Redundancy", ("1_4_2",)),
            ("ResolutionStep", ("1_0_1",)),
            ("Resource", ("1_19_0",)),
            ("Schedule", ("1_2_5",)),
            ("Sensor", ("1_9_0",)),
            ("Signature", ("1_0_3",)),
            ("SoftwareInventory", ("1_10_2",)),
            ("Storage", ("1_16_0",)),
            ("StorageReplicaInfo", ("1_3_0", "1_4_0")),
            ("VLanNetworkInterface", ("1_3_1",)),
            ("Volume", ("1_10_0",)),
        ]
    )

    def fixDellOemEnclosureChassis(self, ctx: aiopenapi3.plugin.Document.Context) -> aiopenapi3.plugin.Document.Context:
        """
        DellOemEnclosureChassis lacks DellChassis
        """
        if ctx.url.path.startswith("/redfish/v1/Schemas/DellOemEnclosureChassis.v"):
            root, _, version = Path(ctx.url.path).stem.partition(".")
            if (e := f"{root}_{version}_{root}") in ctx.document["components"]["schemas"]:
                v = ctx.document["components"]["schemas"][e]["properties"]
                v["DellChassis"] = {"$ref": "/redfish/v1/DellChassis.yaml#/components/schemas/DellChassis_DellChassis"}

    def fixDellChassis(self, ctx: aiopenapi3.plugin.Document.Context) -> aiopenapi3.plugin.Document.Context:
        if ctx.url.path.endswith("Chassis.v1_25_1.yaml"):
            ctx.document["components"]["schemas"]["Chassis_v1_25_1_Chassis_Oem"]["properties"]["Dell"] = {
                "$ref": "/redfish/v1/DellOemChassis.v1_2_0.yaml#/components/schemas/DellOemChassis_v1_2_0_DellOemChassis"
            }

        if ctx.url.path.endswith("DellOemChassis.v1_2_0.yaml"):
            ctx.document["components"]["schemas"]["DellOemChassis_v1_2_0_DellOemChassis"]["properties"][
                "DellChassis"
            ] = {"$ref": "/redfish/v1/DellChassis.v1_0_0.yaml#/components/schemas/DellChassis_v1_0_0_DellChassis"}

    def fixDellDrive(self, ctx: aiopenapi3.plugin.Document.Context) -> aiopenapi3.plugin.Document.Context:
        if ctx.url.path.endswith("DellDrive.v1_1_0.yaml"):
            for i in ["DellPhysicalDisk", "DellPCIeSSD"]:
                ctx.document["components"]["schemas"]["DellDrive_v1_1_0_DellDrive"]["properties"][i] = {
                    "$ref": f"/redfish/v1/{i}.yaml#/components/schemas/{i}_{i}"
                }

    def fixDellVolume(self, ctx: aiopenapi3.plugin.Document.Context) -> aiopenapi3.plugin.Document.Context:
        if ctx.url.path.endswith("DellVolume.v1_0_0.yaml"):
            for i in ["DellVirtualDisk"]:
                ctx.document["components"]["schemas"]["DellVolume_v1_0_0_DellVolume"]["properties"][i] = {
                    "$ref": f"/redfish/v1/{i}.yaml#/components/schemas/{i}_{i}"
                }

    def fixDellManagerNetworkProtocol_DellCertificate(
        self, ctx: aiopenapi3.plugin.Document.Context
    ) -> aiopenapi3.plugin.Document.Context:
        if ctx.url.path.endswith("DellManagerNetworkProtocol.yaml"):
            ctx.document["components"]["schemas"]["DellManagerNetworkProtocol_DellCertificate"] = yaml.safe_load(
                io.StringIO(
                    """
            type: object
            additionalProperties: false
            properties: {}
            """
                )
            )

    def parsed(self, ctx: aiopenapi3.plugin.Document.Context) -> aiopenapi3.plugin.Document.Context:
        super().parsed(ctx)
        self.removeInvalidVersions(ctx, self.VERSIONS)

        self.fixDellManagerNetworkProtocol_DellCertificate(ctx)

        self.fixDellManager(ctx)
        self.fixResourceHealth(ctx)
        self.fixTaskService(ctx)
        self.fixDellOemEnclosureChassis(ctx)
        self.fixDellChassis(ctx)
        self.fixDellDrive(ctx)
        self.fixDellVolume(ctx)
