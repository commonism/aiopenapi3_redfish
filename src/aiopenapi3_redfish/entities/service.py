import asyncio

from typing import Optional

import aiopenapi3_redfish.entities.actions
from aiopenapi3_redfish.base import AsyncResourceRoot, AsyncCollection
from aiopenapi3_redfish.oem import Detour


@Detour("/redfish/v1/AccountService")
@Detour("#AccountService..AccountService")
class AsyncAccountService(AsyncResourceRoot):
    class ManagerAccount(AsyncResourceRoot):
        async def setPassword(self, password):
            return await self.patch(data={"Password": password})

    def __init__(self, client: "Client", odata_id_: str):
        AsyncResourceRoot.__init__(self, client, odata_id_)
        self.Accounts: "AsyncAccountService._Accounts" = None

    @classmethod
    async def asyncNew(cls, client: "Client", odata_id_: str):
        obj = await super().asyncNew(client, odata_id_)

    async def asyncInit(self):
        self.Accounts = await AsyncCollection[AsyncAccountService.ManagerAccount]().asyncNew(
            self._client, self._v.Accounts.odata_id_
        )
        return self


@Detour("/redfish/v1/CertificateService")
@Detour("#CertificateService..CertificateService")
class AsyncCertificateService(AsyncResourceRoot):
    async def GenerateCSR(self):
        """
        '#CertificateService.GenerateCSR':
          target: /redfish/v1/CertificateService/Actions/CertificateService.GenerateCSR
        """
        raise NotImplementedError()

    async def ReplaceCertificate(self):
        """
        '#CertificateService.ReplaceCertificate':
          target: /redfish/v1/CertificateService/Actions/CertificateService.ReplaceCertificate
        """
        raise NotImplementedError()


@Detour("#NetworkAdapter..NetworkAdapter")
class NetworkAdapter(AsyncResourceRoot):
    async def asyncInit(self):
        super().asyncInit()
        self.NetworkPorts = await AsyncCollection[AsyncResourceRoot]().asyncNew(
            self._client, self._v.NetworkPorts.odata_id_
        )
        return self


@Detour("/redfish/v1/Chassis/{ChassisId}")
@Detour("#Chassis..Chassis")
class AsyncChassis(AsyncResourceRoot):
    async def asyncInit(self):
        super().asyncInit()
        self.NetworkAdapters = await AsyncCollection[NetworkAdapter]().asyncNew(
            self._client, self._v.NetworkAdapters.odata_id_
        )
        return self

    async def Reset(self, ResetType: str):
        action: aiopenapi3_redfish.entities.actions.Action = self.Actions["#Chassis.Reset"]
        data = action.data.model_validate(dict(ResetType=ResetType))
        return await action(data=data)


@Detour("/redfish/v1/EventService")
@Detour("#EventService..EventService")
class AsyncEventService(AsyncResourceRoot):
    async def SubmitTestEvent(self, EventType: str = "Alert", MessageId: str = "AMP0300", **kwargs):
        action = self.Actions["#EventService.SubmitTestEvent"]
        data = action.data.model_validate(dict(EventType=EventType, MessageId=MessageId, **kwargs))
        r = await action(data=data.model_dump(exclude_unset=True, by_alias=True))
        return


@Detour("/redfish/v1/Fabrics/{FabricId}")
@Detour("#Fabric..Fabric")
class AsyncFabric(AsyncResourceRoot):
    pass


@Detour("/redfish/v1/JobService")
@Detour("#JobService..JobService")
class AsyncJobService(AsyncResourceRoot):
    pass


@Detour("/redfish/v1/LicenseService")
@Detour("#LicenseService..LicenseService")
class AsyncLicenseService(AsyncResourceRoot):
    async def Install(self):
        """
        # LicenseService.Install
        """
        raise NotImplementedError()


@Detour("/redfish/v1/SessionService")
@Detour("#SessionService..SessionService")
class AsyncSessionService(AsyncResourceRoot):
    class AsyncSession(AsyncResourceRoot):
        pass

    async def createSession(self):
        auth = self._client.api._security["basicAuth"]
        req = self._client.api._[("/redfish/v1/SessionService/Sessions", "post")]

        data = {"UserName": auth[0], "Password": auth[1]}
        try:
            self._client.api.authenticate(None)
            headers, value = await req(data=data, return_headers=True)
            self._client.api.authenticate(**{"X-Auth": headers["X-Auth-Token"]})
            self._session = (headers, value)
        except KeyError:
            self._client.api.authenticate(None, basicAuth=self._client.config.auth)
            return None
        return AsyncSessionService.AsyncSession(self._client, value)

    @classmethod
    async def asyncNew(cls, client: "Client", odata_id_: str):
        obj = await super().asyncNew(client, odata_id_)
        await obj.asyncInit()
        return obj

    async def asyncInit(self):
        self.Sessions = await AsyncCollection[AsyncSessionService.AsyncSession]().asyncNew(
            self._client, self._v.Sessions.odata_id_
        )
        return self


@Detour("/redfish/v1/Systems/{SystemId}")
@Detour("#ComputerSystem..ComputerSystem")
class AsyncSystem(AsyncResourceRoot):
    async def Reset(self, ResetType: str):
        action: aiopenapi3_redfish.entities.actions.Action = self.Actions["#ComputerSystem.Reset"]
        data = action.data.model_validate(dict(ResetType=ResetType))
        return await action(data=data)


@Detour("/redfish/v1/TaskService")
@Detour("#TaskService..TaskService")
class AsyncTaskService(AsyncResourceRoot):
    class AsyncTask(AsyncResourceRoot):
        pass

    def __init__(self, client: "Client", odata_id_: str):
        AsyncResourceRoot.__init__(self, client, odata_id_)
        self.Tasks: Optional[AsyncCollection[AsyncTaskService.AsyncTask]] = None

    @classmethod
    async def asyncNew(cls, client: "Client", odata_id_: str):
        obj = await super().asyncNew(client, odata_id_)
        return obj

    async def asyncInit(self):
        self.Tasks = await AsyncCollection[AsyncTaskService.AsyncTask]().asyncNew(self._client, self._v.Tasks.odata_id_)
        return self

    async def wait_for(self, TaskId: str, pollInterval: int = 7, maxWait: int = 700) -> AsyncTask:
        for i in range(maxWait // pollInterval):
            r = await self.Tasks.index(TaskId)
            if r.TaskState == "Running" and r.TaskStatus == "OK":
                await asyncio.sleep(pollInterval)
                continue
            break
        else:
            raise TimeoutError(TaskId)
        return r


@Detour("/redfish/v1/TelemetryService")
@Detour("#TelemetryService..TelemetryService")
class AsyncTelemetryService(AsyncResourceRoot):
    async def ClearMetricReports(self):
        """
        '#TelemetryService.ClearMetricReports':
          target: /redfish/v1/TelemetryService/Actions/TelemetryService.ClearMetricReports
        """
        raise NotImplementedError()

    async def ResetMetricReportDefinitionsToDefaults(self):
        """
        '#TelemetryService.ResetMetricReportDefinitionsToDefaults':
          target: /redfish/v1/TelemetryService/Actions/TelemetryService.ResetMetricReportDefinitionsToDefaults
        """
        raise NotImplementedError()

    async def SubmitTestMetricReport(self):
        """
        '#TelemetryService.SubmitTestMetricReport':
          target: /redfish/v1/TelemetryService/Actions/TelemetryService.SubmitTestMetricReport
        """
        raise NotImplementedError()


@Detour("/redfish/v1/UpdateService")
@Detour("#UpdateService._.UpdateService")
class AsyncUpdateService(AsyncResourceRoot):
    async def SimpleUpdate(self):
        """
        '#UpdateService.SimpleUpdate':
          '@Redfish.OperationApplyTimeSupport':
            '@odata.type': '#Settings.v1_3_5.OperationApplyTimeSupport'
            SupportedValues:
            - Immediate
            - OnReset
            - OnStartUpdateRequest
          TransferProtocol@Redfish.AllowableValues:
          - HTTP
          - NFS
          - CIFS
          - TFTP
          - HTTPS
          target: /redfish/v1/UpdateService/Actions/UpdateService.SimpleUpdate
        """
        raise NotImplementedError()

    async def StartUpdate(self):
        """
        '#UpdateService.StartUpdate':
          target: /redfish/v1/UpdateService/Actions/UpdateService.StartUpdate
        """
        raise NotImplementedError()
