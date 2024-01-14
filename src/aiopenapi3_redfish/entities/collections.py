from aiopenapi3_redfish.base import AsyncCollection, AsyncResourceRoot
from aiopenapi3_redfish.oem import Detour

from .service import AsyncAccountService, AsyncChassis, AsyncFabric, AsyncSystem, AsyncTaskService
from .manager import AsyncManager


@Detour("#ServiceRoot..ServiceRoot/Chassis")
class ChassisCollection(AsyncCollection[AsyncChassis]):
    pass


@Detour("#ServiceRoot..ServiceRoot/Fabrics")
class FabricCollection(AsyncCollection[AsyncFabric]):
    pass


@Detour("#JobService..JobService/Jobs")
class JobCollection(AsyncCollection[AsyncResourceRoot]):
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


@Detour("#SessionService..SessionService/Sessions")
class SessionsCollection(AsyncCollection[AsyncResourceRoot]):
    pass


@Detour("#ServiceRoot..ServiceRoot/Systems")
class SystemsCollection(AsyncCollection[AsyncSystem]):
    pass


@Detour("#TaskService..TaskService/Tasks")
class TaskCollection(AsyncCollection[AsyncTaskService.AsyncTask]):
    pass
