import typing

import aiopenapi3.plugin

from ..base import _DocumentBase

if typing.TYPE_CHECKING:
    pass


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
