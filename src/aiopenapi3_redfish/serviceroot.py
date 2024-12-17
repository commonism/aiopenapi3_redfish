import typing
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

if typing.TYPE_CHECKING:
    from .client import AsyncClient


@Detour("/redfish/v1")
@Detour("#ServiceRoot..ServiceRoot")
class AsyncServiceRoot(AsyncResourceRoot):
    AccountService: AsyncAccountService
    CertificateService: AsyncCertificateService
    Chassis: AsyncCollection[AsyncChassis]
    EventService: AsyncEventService
    Fabrics: AsyncCollection[AsyncFabric]
    Managers: AsyncCollection[AsyncManager]
    Manager: AsyncManager | None
    Tasks: AsyncTaskService
    TelemetryService: AsyncTelemetryService
    UpdateService: AsyncUpdateService
    SessionService: AsyncSessionService
    Systems: AsyncCollection[AsyncSystem]

    @classmethod
    async def asyncNew(cls, client: "AsyncClient", odata_id_: str):
        obj = await super().asyncNew(client, odata_id_)
        await obj.asyncInit()
        return obj

    async def asyncInit(self, *paths):
        if (items := self._client._mapping.classFromResourceType(self.odata_type_, None)) is None:
            return

        for field in items.keys():
            if paths and field not in paths:
                continue

            attr, value = await self._getItem(field)
            if value is None:
                continue
            setattr(self, attr, value)
        return self

    @property
    def TaskService(self):
        return self.Tasks
