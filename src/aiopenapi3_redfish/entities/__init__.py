from ..oem import Lookup
from .actions import Actions, Oem

from .service import (
    AsyncAccountService,
    AsyncCertificateService,
    AsyncChassis,
    AsyncEventService,
    AsyncFabric,
    AsyncJobService,
    AsyncLicenseService,
    AsyncSessionService,
    AsyncSystem,
    AsyncTaskService,
    AsyncTelemetryService,
    AsyncUpdateService,
)

from .collections import (
    ChassisCollection,
    FabricCollection,
    JobCollection,
    SessionsCollection,
    SystemsCollection,
    TaskCollection,
    ManagerAccountCollection,
    ManagerCollection,
    NetworkAdapterCollection,
    NetworkDeviceFunctionCollection,
    NetworkPortCollection,
)


from .settings import AsyncBios


class Defaults(Lookup):
    detour = [
        Actions,
        Oem,
        AsyncAccountService,
        AsyncCertificateService,
        AsyncChassis,
        AsyncEventService,
        AsyncFabric,
        AsyncJobService,
        AsyncLicenseService,
        AsyncSessionService,
        AsyncSystem,
        AsyncTaskService,
        AsyncTelemetryService,
        AsyncUpdateService,
        ChassisCollection,
        FabricCollection,
        JobCollection,
        SessionsCollection,
        SystemsCollection,
        TaskCollection,
        ManagerAccountCollection,
        ManagerCollection,
        NetworkAdapterCollection,
        NetworkDeviceFunctionCollection,
        NetworkPortCollection,
        AsyncBios,
    ]
