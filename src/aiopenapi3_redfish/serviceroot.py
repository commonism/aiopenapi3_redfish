from typing import Optional
from .base import AsyncCollection, AsyncResourceRoot

from aiopenapi3_redfish.entities.service import (
    AsyncAccountService,
    AsyncCertificateService,
    AsyncChassis,
    AsyncEventService,
    AsyncFabric,
    AsyncSessionService,
    AsyncSystem,
    AsyncTaskService,
    AsyncTelemetryService,
    AsyncUpdateService,
)
from aiopenapi3_redfish.entities.manager import AsyncManager
from aiopenapi3_redfish.oem import Detour


@Detour("/redfish/v1")
@Detour("#ServiceRoot..ServiceRoot")
class AsyncServiceRoot(AsyncResourceRoot):
    AccountService: AsyncAccountService
    CertificateService: AsyncCertificateService
    Chassis: AsyncCollection[AsyncChassis]
    EventService: AsyncEventService
    Fabrics: AsyncCollection[AsyncFabric]
    Managers: AsyncCollection[AsyncManager]
    Manager: Optional[AsyncManager]
    TaskService: AsyncTaskService
    TelemetryService: AsyncTelemetryService
    UpdateService: AsyncUpdateService
    SessionService: AsyncSessionService
    Systems: AsyncCollection[AsyncSystem]

    @classmethod
    async def asyncNew(cls, client: "Client", odata_id_: str):
        obj = await super().asyncNew(client, odata_id_)
        await obj.asyncInit()
        return obj

    async def asyncInit(self):
        client = self._client
        self.AccountService = await AsyncResourceRoot.asyncNew(client, self._v.AccountService.odata_id_)
        self.CertificateService = await AsyncResourceRoot.asyncNew(client, self._v.CertificateService.odata_id_)
        self.Chassis = await AsyncCollection[AsyncChassis]().asyncNew(client, self._v.Chassis.odata_id_)
        self.EventService = await AsyncResourceRoot.asyncNew(client, self._v.EventService.odata_id_)
        self.Fabrics = await AsyncCollection[AsyncFabric]().asyncNew(client, self._v.Managers.odata_id_)
        self.Managers = await AsyncCollection[AsyncManager]().asyncNew(client, self._v.Managers.odata_id_)
        self.Manager = None
        self.TaskService = await AsyncResourceRoot.asyncNew(client, self._v.Tasks.odata_id_)
        self.TelemetryService = await AsyncResourceRoot.asyncNew(client, self._v.TelemetryService.odata_id_)
        self.UpdateService = await AsyncResourceRoot.asyncNew(client, self._v.UpdateService.odata_id_)
        self.SessionService = await AsyncResourceRoot.asyncNew(client, self._v.SessionService.odata_id_)
        self.Systems = await AsyncCollection[AsyncSystem]().asyncNew(client, self._v.Systems.odata_id_)
        return self
