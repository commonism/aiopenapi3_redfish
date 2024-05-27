from aiopenapi3_redfish.base import AsyncCollection, AsyncResourceRoot
from aiopenapi3_redfish.oem import Detour

from .service import AsyncAccountService, AsyncChassis, AsyncFabric, AsyncSystem, AsyncTaskService
from .manager import AsyncManager


@Detour("#ServiceRoot..ServiceRoot/Chassis")
class ChassisCollection(AsyncCollection[AsyncChassis]):
    pass


@Detour("#Fabric..Fabric/Connections")
class ConnectionCollection(AsyncCollection[AsyncResourceRoot]):
    pass


@Detour("#Storage..Storage/Drives")
class DriveCollection(AsyncCollection[AsyncResourceRoot]):
    pass


@Detour("#Fabric..Fabric/Endpoints")
class EndpointCollection(AsyncCollection[AsyncResourceRoot]):
    pass


@Detour("#Fabric..Fabric/EndpointGroups")
class EndpointGroupCollection(AsyncCollection[AsyncResourceRoot]):
    pass


@Detour("#Manager..Manager/EthernetInterfaces")
@Detour("#NetworkDeviceFunction..NetworkDeviceFunction/Ethernet/EthernetInterfaces")
class EthernetInterfaceCollection(AsyncCollection[AsyncResourceRoot]):
    pass


@Detour("#ServiceRoot..ServiceRoot/Fabrics")
class FabricCollection(AsyncCollection[AsyncFabric]):
    pass


@Detour("#JobService..JobService/Jobs")
class JobCollection(AsyncCollection[AsyncResourceRoot]):
    pass


@Detour("#LogService..LogService/Entries")
class LogEntryCollection(AsyncCollection[AsyncResourceRoot]):
    pass


@Detour("#Manager..Manager/LogServices")
class LogServiceCollection(AsyncCollection[AsyncResourceRoot]):
    pass


@Detour("#AccountService..AccountService/Accounts")
class ManagerAccountCollection(AsyncCollection[AsyncAccountService.ManagerAccount]):
    pass


@Detour("#ServiceRoot..ServiceRoot/Managers")
class ManagerCollection(AsyncCollection[AsyncManager]):
    pass


@Detour("#Chassis..Chassis/NetworkAdapters")
class NetworkAdapterCollection(AsyncCollection[AsyncResourceRoot]):
    pass


@Detour("#NetworkAdapter..NetworkAdapter/NetworkPorts")
class NetworkPortCollection(AsyncCollection[AsyncResourceRoot]):
    pass


@Detour("#NetworkAdapter..NetworkAdapter/Ports")
@Detour("#Switch..Switch/Ports")
class PortCollection(AsyncCollection[AsyncResourceRoot]):
    pass


@Detour("#NetworkAdapter..NetworkAdapter/NetworkDeviceFunctions")
class NetworkDeviceFunctionCollection(AsyncCollection[AsyncResourceRoot]):
    pass


@Detour("#SessionService..SessionService/Sessions")
class SessionsCollection(AsyncCollection[AsyncResourceRoot]):
    pass


@Detour("#StorageCollection..StorageCollection")
@Detour("#ServiceRoot..ServiceRoot/Storage")
class StorageCollection(AsyncCollection[AsyncResourceRoot]):
    pass


@Detour("#Storage..Storage/Controllers")
@Detour("#StorageControllerCollection..StorageControllerCollection")
class StorageControllerCollection(AsyncCollection[AsyncResourceRoot]):
    pass


@Detour("#Fabric..Fabric/Switches")
class SwitchCollection(AsyncCollection[AsyncResourceRoot]):
    pass


@Detour("#ServiceRoot..ServiceRoot/Systems")
class SystemsCollection(AsyncCollection[AsyncSystem]):
    pass


@Detour("#TaskService..TaskService/Tasks")
class TaskCollection(AsyncCollection[AsyncTaskService.AsyncTask]):
    def index(self, key) -> AsyncTaskService.AsyncTask | bytes:
        return super().index(key)


@Detour("#Storage..Storage/Volumes")
class VolumeCollection(AsyncCollection[AsyncResourceRoot]):
    pass


@Detour("#Fabric..Fabric/Zones")
class ZoneCollection(AsyncCollection[AsyncResourceRoot]):
    pass
