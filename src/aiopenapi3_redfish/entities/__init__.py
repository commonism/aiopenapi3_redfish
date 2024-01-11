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
    SessionsCollection,
    SystemsCollection,
    TaskCollection,
    ManagerAccountCollection,
    ManagerCollection,
    NetworkAdapterCollection,
    NetworkPortCollection,
)


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
        SessionsCollection,
        SystemsCollection,
        TaskCollection,
        ManagerAccountCollection,
        ManagerCollection,
        NetworkAdapterCollection,
        NetworkPortCollection,
    ]
