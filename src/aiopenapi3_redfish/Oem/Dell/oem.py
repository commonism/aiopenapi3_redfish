from aiopenapi3_redfish.base import Entity, Actions
from aiopenapi3_redfish.oem import Oem, Routes


@Routes("/redfish/v1/Managers/{ManagerId}/Oem/Dell/DellAttributes/{DellAttributesId}")
class DellAttributes(Entity, Actions):
    pass


@Routes(
    "/redfish/v1/Managers/{ManagerId}/Actions/Oem/EID_674_Manager.ExportSystemConfiguration",
    "/redfish/v1/Managers/{ManagerId}/Actions/Oem/EID_674_Manager.ImportSystemConfiguration",
    "/redfish/v1/Managers/{ManagerId}/Actions/Oem/EID_674_Manager.ImportSystemConfigurationPreview",
)
class EID_674(Entity, Actions):
    pass


@Routes("/redfish/v1/UpdateService/Actions/Oem/DellUpdateService.Install")
class DellUpdateService(Entity, Actions):
    pass


@Routes("/redfish/v1/UpdateService/Actions/Oem/DellTelemetryService.SubmitMetricValue")
class DellTelemetryService(Entity, Actions):
    pass


@Routes(
    "/redfish/v1/Managers/{ManagerId}/Actions/Oem/DellManager.ResetToDefaults",
    "/redfish/v1/Managers/{ManagerId}/Actions/Oem/DellManager.SetCustomDefaults",
)
class DellManager(Entity, Actions):
    pass


DellOem = [DellAttributes, EID_674, DellUpdateService, DellTelemetryService, DellManager]
