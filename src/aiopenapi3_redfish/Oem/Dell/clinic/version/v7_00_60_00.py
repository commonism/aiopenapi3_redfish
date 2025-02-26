import typing

import aiopenapi3.plugin

from ..base import _DocumentBase

if typing.TYPE_CHECKING:
    pass


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
