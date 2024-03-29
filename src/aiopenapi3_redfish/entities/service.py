import asyncio
from typing import Literal

import aiopenapi3.errors

import aiopenapi3_redfish.entities.actions
from aiopenapi3_redfish.base import AsyncResourceRoot, AsyncCollection
from aiopenapi3_redfish.oem import Detour


@Detour("/redfish/v1/AccountService")
@Detour("#AccountService..AccountService")
@Detour("#ServiceRoot..ServiceRoot/AccountService")
class AsyncAccountService(AsyncResourceRoot):
    class ManagerAccount(AsyncResourceRoot):
        async def setPassword(self, password):
            return await self.patch(data={"Password": password})


@Detour("/redfish/v1/CertificateService")
@Detour("#CertificateService..CertificateService")
@Detour("#ServiceRoot..ServiceRoot/CertificateService")
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


@Detour("/redfish/v1/Chassis/{ChassisId}")
@Detour("#Chassis..Chassis")
class AsyncChassis(AsyncResourceRoot):
    async def Reset(self, ResetType: str):
        action: aiopenapi3_redfish.entities.actions.Action = self.Actions["#Chassis.Reset"]
        data = action.data.model_validate(dict(ResetType=ResetType))
        return await action(data=data)


@Detour("/redfish/v1/EventService")
@Detour("#EventService..EventService")
@Detour("#ServiceRoot..ServiceRoot/EventService")
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
@Detour("#ServiceRoot..ServiceRoot/JobService")
class AsyncJobService(AsyncResourceRoot):
    async def wait_for(self, *JobIds: str, pollInterval: int = 7, maxWait: int = 700) -> AsyncResourceRoot:
        todo = set(JobIds)
        done = list()
        error = list()

        while len(todo):
            for JobId in list(todo):
                print(f"{len(todo)=} {len(done)=} {len(error)=}")
                job = await self.Jobs.index(JobId)
                if job.JobStatus != "OK":
                    error.append(job)
                else:
                    if job.JobState == "Completed":
                        print(job)
                        done.append(job)
                    elif job.JobState in ("Running", "Scheduled"):
                        await asyncio.sleep(pollInterval)
                        continue
                    else:
                        await asyncio.sleep(pollInterval)
                        continue
                await asyncio.sleep(pollInterval)
                todo.discard(JobId)

        return todo, done, error


@Detour("/redfish/v1/LicenseService")
@Detour("#LicenseService..LicenseService")
@Detour("#ServiceRoot..ServiceRoot/LicenseService")
class AsyncLicenseService(AsyncResourceRoot):
    async def Install(self):
        """
        # LicenseService.Install
        """
        raise NotImplementedError()


@Detour("/redfish/v1/SessionService")
@Detour("#SessionService..SessionService")
@Detour("#ServiceRoot..ServiceRoot/SessionService")
class AsyncSessionService(AsyncResourceRoot):
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
        return AsyncResourceRoot(self._client, value)


@Detour("/redfish/v1/Systems/{SystemId}")
@Detour("#ComputerSystem..ComputerSystem")
class AsyncSystem(AsyncResourceRoot):
    async def Reset(
        self,
        ResetType: Literal[
            "ForceOff",
            "ForceOff",
            "ForceRestart",
            "GracefulRestart",
            "GracefulShutdown",
            "Nmi",
            "On",
            "PowerCycle",
            "PushPowerButton",
        ],
    ):
        self._client.log.info(f"Action #ComputerSystem.Reset {ResetType}")
        action: aiopenapi3_redfish.entities.actions.Action = self.Actions["#ComputerSystem.Reset"]
        data = action.data.model_validate(dict(ResetType=ResetType))
        r = await action(data=data.model_dump(exclude_unset=True, by_alias=True))
        return r

    async def togglePower(self, powerState=None):
        if powerState is None:
            await self.refresh()
            powerState = self.PowerState

        state = {"On": "Off", "Off": "On"}[powerState]

        self._client.log.info(f"togglePower {powerState} -> {state}")

        async def pollState():
            while self.PowerState != state:
                await asyncio.sleep(15)
                try:
                    await self.refresh()
                except aiopenapi3.errors.ResponseSchemaError:
                    pass

        if state == "Off":
            if self.PowerState != "Off":
                await self.Reset("GracefulShutdown")
                try:
                    await asyncio.wait_for(pollState(), 600)
                except TimeoutError:
                    await self.Reset("ForceOff")
        elif state == "On":
            try:
                if self.PowerState == "Off":
                    await self.Reset("On")
                await asyncio.wait_for(pollState(), 600)
            except TimeoutError:
                await self.Reset("ForceRestart")

        await self.refresh()
        assert self.PowerState == state


@Detour("/redfish/v1/TaskService")
@Detour("#TaskService..TaskService")
@Detour("#ServiceRoot..ServiceRoot/Tasks")
class AsyncTaskService(AsyncResourceRoot):
    class AsyncTask(AsyncResourceRoot):
        pass

    async def wait_for(self, TaskId: str, pollInterval: int = 7, maxWait: int = 700) -> AsyncTask:
        for i in range(maxWait // pollInterval):
            r = await self.Tasks.index(TaskId)
            if not isinstance(r, AsyncResourceRoot):
                raise TypeError(r)
            if r.TaskState == "Running" and r.TaskStatus == "OK":
                await asyncio.sleep(pollInterval)
                continue
            break
        else:
            raise TimeoutError(TaskId)
        return r


@Detour("/redfish/v1/TelemetryService")
@Detour("#TelemetryService..TelemetryService")
@Detour("#ServiceRoot..ServiceRoot/TelemetryService")
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
@Detour("#ServiceRoot..ServiceRoot/UpdateService")
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
