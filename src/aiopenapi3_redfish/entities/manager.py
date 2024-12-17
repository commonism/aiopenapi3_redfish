import yarl

from aiopenapi3_redfish.base import AsyncResourceRoot, AsyncCollection
from aiopenapi3_redfish.entities.actions import Action


class AsyncManager(AsyncResourceRoot):
    async def Reset(self):
        """
        '#Manager.Reset':
          ResetType@Redfish.AllowableValues:
          - GracefulRestart
          target: /redfish/v1/Managers/iDRAC.Embedded.1/Actions/Manager.Reset
        """
        action: Action = self.Actions["#Manager.Reset"]
        data = action.data.model_validate(dict(ResetType="GracefulRestart"))
        return await action(data=data)

        await self.Actions["#Manager.Reset"]()

    async def ResetToDefaults(self):
        """
        '#Manager.ResetToDefaults':
          ResetType@Redfish.AllowableValues:
          - ResetAll
          - PreserveNetworkAndUsers
          target: /redfish/v1/Managers/iDRAC.Embedded.1/Actions/Manager.ResetToDefaults

        """
        raise NotImplementedError()
