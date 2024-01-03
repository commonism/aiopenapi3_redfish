import copy

from .base import AsyncResourceRoot, AsyncCollection, AsyncActions


class AsyncAccountService(AsyncResourceRoot):
    class ManagerAccount(AsyncResourceRoot):
        async def setPassword(self, password):
            return await self.patch(data={"Password": password})

    def __init__(self, client: "Client", odata_id_: str):
        AsyncResourceRoot.__init__(self, client, odata_id_)
        self.Accounts: "AsyncAccountService._Accounts" = None

    @classmethod
    async def asyncInit(cls, client: "Client", odata_id_: str):
        obj = await super().asyncInit(client, odata_id_)
        obj.Accounts = await AsyncCollection[AsyncAccountService.ManagerAccount]().asyncInit(
            client, obj._v.Accounts.odata_id_
        )
        return obj


class AsyncCertificateService(AsyncResourceRoot, AsyncActions):
    pass


class AsyncChassis(AsyncResourceRoot):
    pass


class AsyncEventService(AsyncResourceRoot, AsyncActions):
    pass


class AsyncFabrics(AsyncResourceRoot):
    pass


class AsyncJobService(AsyncResourceRoot):
    pass


class AsyncLicenseService(AsyncResourceRoot):
    pass


class AsyncSessionService(AsyncResourceRoot):
    class AsyncSession(AsyncResourceRoot):
        pass

    async def createSession(self):
        auth = copy.copy(self._client.api._security["basicAuth"])
        req = self._client.api._[("/redfish/v1/SessionService/Sessions", "post")]

        data = {"UserName": auth[0], "Password": auth[1]}
        try:
            self._client.api.authenticate(None)
            headers, value = await req(data=data, return_headers=True)
            self._client.api.authenticate(**{"X-Auth": headers["X-Auth-Token"]})
            self._session = (headers, value)
        except KeyError:
            self._client.api.authenticate(None)
            self._client.api.authenticate(basicAuth=auth)
            return None
        return AsyncSessionService.AsyncSession(self._client, value)

    @classmethod
    async def asyncInit(cls, client: "Client", odata_id_: str):
        obj = await super().asyncInit(client, odata_id_)
        obj.Sessions = await AsyncCollection[AsyncSessionService.AsyncSession]().asyncInit(
            client, obj._v.Sessions.odata_id_
        )
        return obj


class AsyncSystems(AsyncResourceRoot):
    pass


class AsyncTaskService(AsyncResourceRoot):
    class Tasks_(AsyncResourceRoot):
        pass

    def __init__(self, client: "Client", odata_id_: str):
        AsyncResourceRoot.__init__(self, client, odata_id_)
        self.Tasks: "AsyncTaskService.Tasks_" = None

    @classmethod
    async def asyncInit(cls, client: "Client", odata_id_: str):
        obj = await super().asyncInit(client, odata_id_)
        obj.Tasks = await AsyncCollection[AsyncTaskService.Tasks_]().asyncInit(client, obj._v.Tasks.odata_id_)
        return obj

    async def wait_for(self, TaskId: str, pollInterval=7, maxWait=700) -> Tasks_:
        for i in range(maxWait // pollInterval):
            r = await self.Tasks.index(TaskId)
            if r.TaskState == "Running" and r.TaskStatus == "OK":
                await asyncio.sleep(pollInterval)
                continue
            break
        else:
            raise TimeoutError(TaskId)
        return r


class AsyncTelemetryService(AsyncResourceRoot, AsyncActions):
    pass


class AsyncUpdateService(AsyncResourceRoot, AsyncActions):
    pass
