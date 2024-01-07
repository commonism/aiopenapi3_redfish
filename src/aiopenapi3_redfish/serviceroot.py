from .base import AsyncCollection, AsyncResourceRoot

from .service import (
    AsyncAccountService,
    AsyncCertificateService,
    AsyncChassis,
    AsyncEventService,
    AsyncSessionService,
    AsyncSystem,
    AsyncTaskService,
    AsyncTelemetryService,
    AsyncUpdateService,
)
from .manager import AsyncManager


class AsyncServiceRoot(AsyncResourceRoot):
    AccountService: AsyncAccountService
    CertificateService: AsyncCertificateService
    Chassis: AsyncCollection[AsyncChassis]
    EventService: AsyncEventService
    Managers: AsyncCollection[AsyncManager]
    Manager: AsyncManager
    TaskService: AsyncTaskService
    TelemetryService: AsyncTelemetryService
    UpdateService: AsyncUpdateService
    SessionService: AsyncSessionService
    Systems: AsyncCollection[AsyncSystem]

    @classmethod
    async def asyncInit(cls, client: "Client", odata_id_: str):
        obj = await super().asyncInit(client, odata_id_)

        obj.AccountService = await AsyncAccountService.asyncInit(client, obj._v.AccountService.odata_id_)
        obj.CertificateService = await AsyncCertificateService.asyncInit(client, obj._v.CertificateService.odata_id_)
        obj.Chassis = await AsyncCollection[AsyncChassis]().asyncInit(client, obj._v.Chassis.odata_id_)
        obj.EventService = await AsyncEventService.asyncInit(client, obj._v.EventService.odata_id_)
        obj.Managers = await AsyncCollection[AsyncManager]().asyncInit(client, obj._v.Managers.odata_id_)
        obj.Manager = await obj.Managers.first()
        obj.TaskService = await AsyncTaskService.asyncInit(client, obj._v.Tasks.odata_id_)
        obj.TelemetryService = await AsyncTelemetryService.asyncInit(client, obj._v.TelemetryService.odata_id_)
        obj.UpdateService = await AsyncUpdateService.asyncInit(client, obj._v.UpdateService.odata_id_)
        obj.SessionService = await AsyncSessionService.asyncInit(client, obj._v.SessionService.odata_id_)
        obj.Systems = await AsyncCollection[AsyncSystem]().asyncInit(client, obj._v.Systems.odata_id_)

        return obj
