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
    ]
