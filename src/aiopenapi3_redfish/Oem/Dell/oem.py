import collections
import enum

import jq
import yarl

from aiopenapi3_redfish.base import AsyncResourceRoot, ResourceItem, AsyncCollection
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


@Detour("#Manager..Manager/Links/Oem")
class ManagerLinksOem(ResourceItem):
    def __init__(self, root, path, value):
        super().__init__(root, path, value)


@Detour("#DellOem..DellOemLinks")
class DellOemLinks(ResourceItem):
    @property
    def DellAttributes(self):
        cls = (
            self._root._client.api._documents[yarl.URL("/redfish/v1/Schemas/odata-v4.yaml")]
            .components.schemas["odata-v4_idRef"]
            .get_type()
        )
        data = [cls.model_validate(i) for i in self._v["DellAttributes"]]

        c = AsyncCollection[DellAttributes](client=self._root._client, data=data)
        return c


@Detour(
    "#DellAttributes.v1_0_0.DellAttributes",
    "/redfish/v1/Managers/{ManagerId}/Oem/Dell/DellAttributes/{DellAttributesId}",
)
class DellAttributes(AsyncResourceRoot):
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
    "/redfish/v1/Managers/{ManagerId}/Actions/Oem/EID_674_Manager.ImportSystemConfigurationPreview",
)
class EID_674_Manager_ImportSystemConfiguration(aiopenapi3_redfish.entities.actions.Action):
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


class DellOem(Oem):
    detour = [
        iDRACServiceRoot,
        DellAttributes,
        EID_674_Manager_ExportSystemConfiguration,
        DellUpdateService,
        DellTelemetryService,
        DellManager,
        ManagerLinksOem,
        DellOemLinks,
        ManagerActionsOem,
    ]
