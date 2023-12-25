from pathlib import Path
import copy

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
            set the PathItems security to basicAuth instead of X-Auth AND basicAuth
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

        return ctx


class RoutingContext:
    pass


def Routes(*args):
    def x(*args, **kwargs):
        return None

    return x


class Message(aiopenapi3.plugin.Message):
    def parsed(self, ctx: "Message.Context") -> "Message.Context":
        pass

    @Routes("/redfish/v1/Systems")
    async def _handle_Systems(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Systems/{ComputerSystemId}")
    async def _handle_System(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Systems/{ComputerSystemId}/Processors")
    async def _handle_Processors(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Systems/{ComputerSystemId}/Processors/{ProcessorId}")
    async def _handle_Processor(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Systems/{ComputerSystemId}/Memory")
    async def _handle_MemoryCollection(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Systems/{ComputerSystemId}/Memory/{MemoryId}")
    async def _handle_Memory(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Systems/{ComputerSystemId}/Storage")
    async def _handle_StorageCollection(self, page: RoutingContext):
        for i in page.data.Members:
            await self.visit(i.odata_id_)

    @Routes("/redfish/v1/Systems/{ComputerSystemId}/Storage/{StorageId}")
    async def _handle_Storage(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Chassis")
    async def _handle_ChassisCollection(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Chassis/{ChassisId}")
    async def _handle_Chassis(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Chassis/{ChassisId}/Power")
    async def _handle_Power(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Managers")
    async def _handle_Managers(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Managers/{ManagerId}")
    async def _handle_Manager(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Managers/{ManagerId}/NetworkProtocol")
    async def _handle_NetworkProtocol(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/TaskService")
    async def _handle_TaskService(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/TaskService/Tasks")
    async def _handle_Tasks(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/SessionService")
    async def _handle_SessionService(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/AccountService")
    async def _handle_AccountService(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/EventService")
    async def _handle_EventService(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Registries")
    async def _handle_Registries(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Registries/{MessageRegistryFileId}")
    async def _handle_MessageRegistryFile(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/JsonSchemas")
    async def _handle_JsonSchemas(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Systems/{ComputerSystemId}/Storage/{StorageId}/Volumes")
    async def _handle_Volumes(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Systems/{ComputerSystemId}/Storage/{StorageId}/Volumes/{VolumeId}")
    async def _handle_Volume(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Systems/{ComputerSystemId}/Storage/Drives/{DriveId}")
    @Routes("/redfish/v1/Systems/{ComputerSystemId}/Storage/{StorageId}/Drives/{DriveId}")
    async def _handle_Drive(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Systems/{ComputerSystemId}/SimpleStorage")
    async def _handle_SimpleStorageCollection(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Systems/{ComputerSystemId}/SimpleStorage/{SimpleStorageId}")
    async def _handle_SimpleStorage(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Systems/{ComputerSystemId}/NetworkInterfaces")
    async def _handle_NetworkInterfaces(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Systems/{ComputerSystemId}/NetworkInterfaces/{NetworkInterfaceId}")
    async def _handle_NetworkInterface(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Chassis/{ChassisId}/NetworkAdapters/{NetworkAdapterId}")
    async def _handle_NetworkAdapter(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Chassis/{ChassisId}/NetworkAdapters/{NetworkAdapterId}/NetworkPorts")
    async def _handle_NetworkPorts(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Chassis/{ChassisId}/NetworkAdapters/{NetworkAdapterId}/NetworkPorts/{NetworkPortId}")
    async def _handle_NetworkPort(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Chassis/{ChassisId}/NetworkAdapters/{NetworkAdapterId}/NetworkDeviceFunctions")
    async def _handle_NetworkDeviceFunctions(self, page: RoutingContext):
        pass

    @Routes(
        "/redfish/v1/Chassis/{ChassisId}/NetworkAdapters/{NetworkAdapterId}/NetworkDeviceFunctions/{NetworkDeviceFunctionId}"
    )
    async def _handle_NetworkDeviceFunction(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Systems/{ComputerSystemId}/EthernetInterfaces")
    @Routes("/redfish/v1/Managers/{ManagerId}/EthernetInterfaces")
    async def _handle_EthernetInterfaces(self, page: RoutingContext):
        pass

    @Routes("/redfish/v1/Systems/{ComputerSystemId}/EthernetInterfaces/{EthernetInterfaceId}")
    @Routes("/redfish/v1/Managers/{ManagerId}/EthernetInterfaces/{EthernetInterfaceId}")
    async def _handle_EthernetInterface(self, page: RoutingContext):
        pass

    # 6.91 ProcessorMetrics 1.6.0
    @Routes(
        "/redfish/v1/Systems/{ComputerSystemId}/Processors/{ProcessorId}/ProcessorMetrics",
        "/redfish/v1/Systems/{ComputerSystemId}/Processors/{ProcessorId}/SubProcessors/{ProcessorId2}/ProcessorMetrics",
        "/redfish/v1/Systems/{ComputerSystemId}/Processors/{ProcessorId}/SubProcessors/{ProcessorId2}/SubProcessors/{ProcessorId3}/ProcessorMetrics",
        "/redfish/v1/Systems/{ComputerSystemId}/ProcessorSummary/ProcessorMetrics",
    )

    # 6.90 Processor 1.16.0
    @Routes(
        "/redfish/v1/Systems/{ComputerSystemId}/Processors/{ProcessorId}",
        "/redfish/v1/Systems/{ComputerSystemId}/Processors/{ProcessorId}/SubProcessors/{ProcessorId2}",
        "/redfish/v1/Systems/{ComputerSystemId}/Processors/{ProcessorId}/SubProcessors/{ProcessorId2}/SubProcessors/{ProcessorId3}",
    )

    # Dell
    @Routes(
        "/redfish/v1/Dell/Chassis/{ChassisId}/DellAssembly/{AssemblyId}",
        "/redfish/v1/Chassis/{ChassisId}/Power/Oem/Dell/DellPowerSupplyInventory/{PowerSupplyId}",
        "/redfish/v1/Managers/{ManagerId}/LogServices/{LogServiceId}/Entries",
    )

    # 6.13 Bios 1.2.0
    @Routes(
        "/redfish/v1/CompositionService/ResourceBlocks/{ResourceBlockId}/Systems/{ComputerSystemId}/Bios",
        "/redfish/v1/ResourceBlocks/{ResourceBlockId}/Systems/{ComputerSystemId}/Bios",
        "/redfish/v1/Systems/{ComputerSystemId}/Bios",
    )

    # 6.14 BootOption 1.0.4
    @Routes(
        "/redfish/v1/CompositionService/ResourceBlocks/{ResourceBlockId}/Systems/{ComputerSystemId}/BootOptions/{BootOptionId}",
        "/redfish/v1/ResourceBlocks/{ResourceBlockId}/Systems/{ComputerSystemId}/BootOptions/{BootOptionId}",
        "/redfish/v1/Systems/{ComputerSystemId}/BootOptions/{BootOptionId}",
    )

    # PCIeFunctionCollection
    @Routes(
        "/redfish/v1/Chassis/{ChassisId}/PCIeDevices/{PCIeDeviceId}/PCIeFunctions",
        "/redfish/v1/CompositionService/ResourceBlocks/{ResourceBlockId}/Systems/{ComputerSystemId}/PCIeDevices/{PCIeDeviceId}/PCIeFunctions",
        "/redfish/v1/ResourceBlocks/{ResourceBlockId}/Systems/{ComputerSystemId}/PCIeDevices/{PCIeDeviceId}/PCIeFunctions",
        "/redfish/v1/Systems/{ComputerSystemId}/PCIeDevices/{PCIeDeviceId}/PCIeFunctions",
    )

    # LogEntryCollection
    @Routes(
        "/redfish/v1/Chassis/{ChassisId}/LogServices/{LogServiceId}/Entries",
        "/redfish/v1/CompositionService/ResourceBlocks/{ResourceBlockId}/Systems/{ComputerSystemId}/LogServices/{LogServiceId}/Entries",
        "/redfish/v1/JobService/Log/Entries",
        "/redfish/v1/Managers/{ManagerId}/LogServices/{LogServiceId}/Entries",
        "/redfish/v1/ResourceBlocks/{ResourceBlockId}/Systems/{ComputerSystemId}/LogServices/{LogServiceId}/Entries",
        "/redfish/v1/Systems/{ComputerSystemId}/LogServices/{LogServiceId}/Entries",
        "/redfish/v1/Systems/{ComputerSystemId}/Memory/{MemoryId}/DeviceLog/Entries",
        "/redfish/v1/TelemetryService/LogService/Entries",
    )

    # 6.51 LogEntry 1.13.0
    @Routes(
        "/redfish/v1/Chassis/{ChassisId}/LogServices/{LogServiceId}/Entries/{LogEntryId}",
        "/redfish/v1/CompositionService/ResourceBlocks/{ResourceBlockId}/Systems/{ComputerSystemId}/LogServices/{LogServiceId}/Entries/{LogEntryId}",
        "/redfish/v1/JobService/Log/Entries/{LogEntryId}",
        "/redfish/v1/Managers/{ManagerId}/LogServices/{LogServiceId}/Entries/{LogEntryId}",
        "/redfish/v1/ResourceBlocks/{ResourceBlockId}/Systems/{ComputerSystemId}/LogServices/{LogServiceId}/Entries/{LogEntryId}",
        "/redfish/v1/Systems/{ComputerSystemId}/LogServices/{LogServiceId}/Entries/{LogEntryId}",
        "/redfish/v1/Systems/{ComputerSystemId}/Memory/{MemoryId}/DeviceLog/Entries/{LogEntryId}",
        "/redfish/v1/TelemetryService/LogService/Entries/{LogEntryId}",
    )

    # 6.54 ManagerAccount 1.9.0
    @Routes(
        "/redfish/v1/AccountService/Accounts/{ManagerAccountId}",
        "/redfish/v1/Managers/{ManagerId}/RemoteAccountService/Accounts/{ManagerAccountId}",
    )

    # 6.76 PCIeDevice 1.10.0
    @Routes(
        "/redfish/v1/Chassis/{ChassisId}/PCIeDevices/{PCIeDeviceId}",
        "/redfish/v1/CompositionService/ResourceBlocks/{ResourceBlockId}/Systems/{ComputerSystemId}/PCIeDevices/{PCIeDeviceId}",
        "/redfish/v1/ResourceBlocks/{ResourceBlockId}/Systems/{ComputerSystemId}/PCIeDevices/{PCIeDeviceId}",
        "/redfish/v1/Systems/{ComputerSystemId}/PCIeDevices/{PCIeDeviceId}",
    )

    # 6.77 PCIeFunction 1.4.0
    @Routes(
        "/redfish/v1/Chassis/{ChassisId}/PCIeDevices/{PCIeDeviceId}/PCIeFunctions/{PCIeFunctionId}",
        "/redfish/v1/CompositionService/ResourceBlocks/{ResourceBlockId}/Systems/{ComputerSystemId}/PCIeDevices/{PCIeDeviceId}/PCIeFunctions/{PCIeFunctionId}",
        "/redfish/v1/ResourceBlocks/{ResourceBlockId}/Systems/{ComputerSystemId}/PCIeDevices/{PCIeDeviceId}/PCIeFunctions/{PCIeFunctionId}",
        "/redfish/v1/Systems/{ComputerSystemId}/PCIeDevices/{PCIeDeviceId}/PCIeFunctions/{PCIeFunctionId}",
    )

    # 6.98 SecureBootDatabase 1.0.1
    @Routes(
        "/redfish/v1/CompositionService/ResourceBlocks/{ResourceBlockId}/Systems/{ComputerSystemId}/SecureBoot/SecureBootDatabases/{DatabaseId}",
        "/redfish/v1/ResourceBlocks/{ResourceBlockId}/Systems/{ComputerSystemId}/SecureBoot/SecureBootDatabases/{DatabaseId}",
        "/redfish/v1/Systems/{ComputerSystemId}/SecureBoot/SecureBootDatabases/{DatabaseId}",
    )

    # 6.100 Sensor 1.6.0
    @Routes(
        "/redfish/v1/Chassis/{ChassisId}/Sensors/{SensorId}",
        "/redfish/v1/PowerEquipment/FloorPDUs/{PowerDistributionId}/Sensors/{SensorId}",
        "/redfish/v1/PowerEquipment/PowerShelves/{PowerDistributionId}/Sensors/{SensorId}",
        "/redfish/v1/PowerEquipment/RackPDUs/{PowerDistributionId}/Sensors/{SensorId}",
        "/redfish/v1/PowerEquipment/Sensors/{SensorId}",
        "/redfish/v1/PowerEquipment/Switchgear/{PowerDistributionId}/Sensors/{SensorId}",
        "/redfish/v1/PowerEquipment/TransferSwitches/{PowerDistributionId}/Sensors/{SensorId}",
    )
    def __ignore(self):
        pass
