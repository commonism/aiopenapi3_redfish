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
        await super().asyncInit()
        assert self.AccountService
        assert self.CertificateService
        assert self.Chassis
        assert self.EventService
        assert self.Fabrics
        assert self.Managers
        self.Manager = None
        assert self.Tasks
        assert self.TelemetryService
        assert self.UpdateService
        assert self.SessionService
        assert self.Systems
        return self

    @property
    def TaskService(self):
        return self.Tasks
