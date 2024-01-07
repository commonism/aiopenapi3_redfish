import asyncio

from typing import Optional

import aiopenapi3_redfish.actions
from .base import AsyncResourceRoot, AsyncCollection


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


class AsyncChassis(AsyncResourceRoot):
    async def Reset(self, ResetType: str):
        action: aiopenapi3_redfish.actions.Action = self.Actions["#Chassis.Reset"]
        data = action.data.model_validate(dict(ResetType=ResetType))
        return await action(data=data)


class AsyncEventService(AsyncResourceRoot):
    async def SubmitTestEvent(self, EventType: str = "Alert", MessageId: str = "AMP0300", **kwargs):
        action = self.Actions["#EventService.SubmitTestEvent"]
        data = action.data.model_validate(dict(EventType=EventType, MessageId=MessageId, **kwargs))
        r = await action(data=data.model_dump(exclude_unset=True, by_alias=True))
        return


class AsyncFabrics(AsyncResourceRoot):
    pass


class AsyncJobService(AsyncResourceRoot):
    pass


class AsyncLicenseService(AsyncResourceRoot):
    async def Install(self):
        """
        # LicenseService.Install
        """
        raise NotImplementedError()


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
    async def asyncInit(cls, client: "Client", odata_id_: str):
        obj = await super().asyncInit(client, odata_id_)
        obj.Sessions = await AsyncCollection[AsyncSessionService.AsyncSession]().asyncInit(
            client, obj._v.Sessions.odata_id_
        )
        return obj


class AsyncSystem(AsyncResourceRoot):
    async def Reset(self, ResetType: str):
        action: aiopenapi3_redfish.actions.Action = self.Actions["#ComputerSystem.Reset"]
        data = action.data.model_validate(dict(ResetType=ResetType))
        return await action(data=data)


class AsyncTaskService(AsyncResourceRoot):
    class AsyncTask(AsyncResourceRoot):
        pass

    def __init__(self, client: "Client", odata_id_: str):
        AsyncResourceRoot.__init__(self, client, odata_id_)
        self.Tasks: Optional[AsyncCollection[AsyncTaskService.AsyncTask]] = None

    @classmethod
    async def asyncInit(cls, client: "Client", odata_id_: str):
        obj = await super().asyncInit(client, odata_id_)
        obj.Tasks = await AsyncCollection[AsyncTaskService.AsyncTask]().asyncInit(client, obj._v.Tasks.odata_id_)
        return obj

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
