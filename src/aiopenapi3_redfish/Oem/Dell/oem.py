import asyncio
import collections
import enum
from pathlib import Path

import jq
import yarl

import aiopenapi3.errors

from aiopenapi3_redfish.base import AsyncResourceRoot, ResourceItem, AsyncCollection
from aiopenapi3_redfish.entities.settings import AsyncSettings
from aiopenapi3_redfish.serviceroot import AsyncServiceRoot
from aiopenapi3_redfish.oem import Oem, Detour

import aiopenapi3_redfish.entities.actions

from aiopenapi3_redfish.entities.manager import AsyncManager


@Detour("/redfish/v1")
@Detour("#ServiceRoot..ServiceRoot")
class iDRACServiceRoot(AsyncServiceRoot):
    async def asyncInit(self):
        await super().asyncInit()

        async for m in self.Managers.list():
            if m.Id == "iDRAC.Embedded.1":
                break
        else:
            raise KeyError("iDRAC.Embedded")
        self.Manager = m
        return self


@Detour("#Manager..Manager/Actions/Oem")
class ManagerActionsOem(aiopenapi3_redfish.entities.actions.Oem):
    def ExportSystemConfiguration(self) -> aiopenapi3_redfish.entities.actions.Action:
        v = self._v["#OemManager.ExportSystemConfiguration"]
        cls = self._createAction(v["target"], v.get("title", ""), v)
        return cls


@Detour("#DellOem..DellOemLinks")
class DellOemLinks(ResourceItem):
    def __init__(self, root, path, value):
        cls = root._client.api._documents[yarl.URL("/redfish/v1/Schemas/DellOem.v1_3_0.yaml")].components.schemas[
            "DellOem_v1_3_0_DellOemLinks"
        ]
        data = cls.get_type().model_validate(value)
        super().__init__(root, yarl.URL(path), data)


@Detour(
    "#DellAttributes.v1_0_0.DellAttributes",
    "/redfish/v1/Managers/{ManagerId}/Oem/Dell/DellAttributes/{DellAttributesId}",
)
class DellAttributes(AsyncSettings):
    class Permissions(enum.IntFlag):
        """
        Source: Chassis Management Controller Version 1.25 for Dell PowerEdge VRTX RACADM Command Line Reference Guide
        """

        LogintoiDRAC = 0x00000001
        ConfigureiDRAC = 0x00000002
        ConfigureUsers = 0x00000004
        ClearLogs = 0x00000008
        ExecuteServerControlCommands = 0x00000010
        AccessVirtualConsole = 0x00000020
        AccessVirtualMedia = 0x00000040
        TestAlerts = 0x00000080
        ExecuteDebugCommands = 0x00000100

    def list(self):
        r = collections.defaultdict(lambda: collections.defaultdict(dict))

        def compare(kv):
            cls, idx, attr = kv[0]
            return (cls, int(idx), attr)

        for (cls, idx, attr), value in sorted(
            map(lambda kv: (kv[0].split("."), kv[1]), self._v.Attributes.model_extra.items()), key=compare
        ):
            r[cls][idx][attr] = value
        return r

    def filter(self, jq_):
        return jq.compile(jq_).input(self.list())


@Detour("#DellOem..DellOemLinks/DellAttributes")
class DellAttributesCollection(AsyncCollection[DellAttributes]):
    def __init__(self, root, path, value):
        super().__init__(root._client, None)
        self._data = value

    async def index(self, key):
        for i in self._data:
            if Path(i.odata_id_).name == key:
                return await self.T.asyncNew(self._root._client, i.odata_id_)
        raise KeyError(key)


@Detour("#DellOem..DellOemLinks/Jobs")
@Detour("#DellJobCollection.DellJobCollection")
class DellJobCollection(AsyncCollection[AsyncResourceRoot]):
    def __init__(self, root, path, value):
        super().__init__(root._client, value)


@Detour("/redfish/v1/Managers/{ManagerId}/Oem/Dell/Jobs")
class DellJobCollection2(AsyncCollection[AsyncResourceRoot]):
    pass


@Detour(
    "/redfish/v1/Managers/{ManagerId}/Actions/Oem/EID_674_Manager.ExportSystemConfiguration",
)
class EID_674_Manager_ExportSystemConfiguration(aiopenapi3_redfish.entities.actions.Action):
    async def __call__(self, Format="XML", Use="Clone", FileName="test", Target="ALL"):
        tShareParameters = self.data.model_fields["ShareParameters"].annotation
        data = self.data(
            ExportFormat=Format,
            ExportUse=Use,
            IncludeInExport=[],
            ShareParameters=tShareParameters(FileName=FileName, Target=[Target]),
        )

        r = await super().__call__(data=data.model_dump(exclude_unset=True))
        return r

    async def export(self):
        return await self.__call__()


@Detour(
    "/redfish/v1/Managers/{ManagerId}/Actions/Oem/EID_674_Manager.ImportSystemConfiguration",
)
class EID_674_Manager_ImportSystemConfiguration(aiopenapi3_redfish.entities.actions.Action):
    async def __call__(self, path: Path, Target: str = "IDRAC"):
        tShareParameters = self.data.model_fields["ShareParameters"].annotation

        import re

        template = path.read_text()
        template = re.sub(r"(   | \n ?)", "", template)

        data = self.data(
            ExecutionMode="Default",
            HostPowerState="On",
            ImportBuffer=template,
            ShareParameters=tShareParameters(FileName="template.json", Target=[Target]),
            ShutdownType="NoReboot",
            TimeToWait=300,
        )
        r = await super().__call__(data=data.model_dump(exclude_unset=True))
        return r


@Detour(
    "/redfish/v1/Managers/{ManagerId}/Actions/Oem/EID_674_Manager.ImportSystemConfigurationPreview",
)
class EID_674_Manager_ImportSystemConfigurationPreview(aiopenapi3_redfish.entities.actions.Action):
    pass


@Detour("/redfish/v1/UpdateService/Actions/Oem/DellUpdateService.Install")
class DellUpdateService(aiopenapi3_redfish.entities.actions.Action):
    pass


@Detour("/redfish/v1/UpdateService/Actions/Oem/DellTelemetryService.SubmitMetricValue")
class DellTelemetryService(aiopenapi3_redfish.entities.actions.Action):
    pass


@Detour(
    "/redfish/v1/Managers/{ManagerId}/Actions/Oem/DellManager.ResetToDefaults",
    "/redfish/v1/Managers/{ManagerId}/Actions/Oem/DellManager.SetCustomDefaults",
)
class DellManager(aiopenapi3_redfish.entities.actions.Action):
    pass


@Detour("#DellSoftwareInstallationService..DellSoftwareInstallationService")
class DellSoftwareInstallationService(AsyncResourceRoot):
    async def InstallFromRepository(self) -> bool:
        """
        InstallFromRepository helper to prevent stalls

        detect stall as no change in jobs for 15 minutes …
        toggle power …
        repeat …

        success if no jobs remain
        fail after a max of 2 hours
        :return: True on Success, all jobs finished.
                False on Timeout, unfinished jobs
        """
        client = self._client
        self._client.log.info("Action #DellSoftwareInstallationService.InstallFromRepository")

        system = await client.Systems.index("System.Embedded.1")

        await system.togglePower("On")

        action = self.Actions["#DellSoftwareInstallationService.InstallFromRepository"]
        data = action.data.model_validate(
            {
                "ApplyUpdate": "True",
                "IgnoreCertWarning": "On",
                "IPAddress": "downloads.dell.com",
                "ShareType": "HTTPS",
                "RebootNeeded": "True",
            }
        )
        r = await action(data=data.model_dump(exclude_unset=True, by_alias=True))

        return await self._awaitInstall(r.Id)

    async def _awaitInstall(self, initial=None):
        """
        :param initial:
        :return: True if no unfinished jobs remain, else False
        """
        client = self._client
        system = await client.Systems.index("System.Embedded.1")

        done = dict()
        todo = dict()

        if initial is None:
            """pick a random job to start with"""
            jobs = await client.Manager.Links.Oem.Dell.Jobs.refresh()
            i = await jobs.first()
            todo[Path(i.odata_id_).name] = i
        else:
            todo[initial] = await client.Manager.Links.Oem.Dell.Jobs.index(initial)

        async def step() -> bool:
            """
            :return True if finished. False if not stalled
            """
            stalled = True
            while len(todo):
                try:
                    jobs = await client.Manager.Links.Oem.Dell.Jobs.refresh()
                    for i in jobs._data:
                        Id = Path(i.odata_id_).name

                        if Id in done:
                            continue

                        old = job = await client.Manager.Links.Oem.Dell.Jobs.index(Id)
                        if Id not in todo:
                            todo[Id] = job
                        else:
                            old = todo[Id]

                        if old.PercentComplete != job.PercentComplete or old == job:
                            stalled = False
                            self._client.log.info(
                                f"{job.Id}/{job.JobType}/{job.Name} {job.JobState}/#{job.MessageId}/{job.Message} {old.PercentComplete} -> {job.PercentComplete}"
                            )
                        todo[Id] = job

                        if job.PercentComplete == 100:
                            del todo[job.Id]
                            done[job.Id] = job
                    await asyncio.sleep(7)
                except (aiopenapi3.errors.RequestError, aiopenapi3.errors.ResponseError) as e0:
                    self._client.log.exception(e0)
                    await asyncio.sleep(15)
                except Exception as e2:
                    self._client.log.exception(e2)
                if stalled is False:
                    self._client.log.info("step continue")
                    return False
            self._client.log.info("step finished")
            return True

        async def install() -> None:
            while True:
                try:
                    finished = await asyncio.wait_for(step(), timeout=10 * 60)
                except (asyncio.TimeoutError, TimeoutError, asyncio.CancelledError) as e0:
                    self._client.log.info(f"step Timeout {type(e0)}")
                    self._client.log.exception(e0)
                    await system.togglePower()
                except Exception as e1:
                    self._client.log.exception(e1)
                else:
                    if finished is True:
                        self._client.log.info("step Finished")
                        break
                self._client.log.info(f"status {len(todo)=} {len(done)=}")

        try:
            await asyncio.wait_for(install(), timeout=3600 * 2)
        except (asyncio.TimeoutError, TimeoutError):
            self._client.log.info("install Timeout")
            return False
        except Exception as e:
            self._client.log.info("install Error")
            self._client.log.exception(e)
            return False
        else:
            self._client.log.info("install Finished")
        self._client.log.info("install Ended")
        return True


@Detour("#DellSoftwareInstallationService..DellSoftwareInstallationService/Actions")
class DellActions(aiopenapi3_redfish.entities.actions.Actions):
    _detour = None


class DellOem(Oem):
    detour = [
        iDRACServiceRoot,
        DellAttributesCollection,
        DellJobCollection,
        DellJobCollection2,
        DellAttributes,
        EID_674_Manager_ImportSystemConfiguration,
        EID_674_Manager_ExportSystemConfiguration,
        DellUpdateService,
        DellTelemetryService,
        DellManager,
        #        ManagerLinksOem,
        DellOemLinks,
        ManagerActionsOem,
        DellSoftwareInstallationService,
        DellActions,
    ]
