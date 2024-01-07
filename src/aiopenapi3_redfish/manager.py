import yarl

from .base import AsyncResourceRoot, AsyncCollection


class AsyncManager(AsyncResourceRoot):
    async def Reset(self):
        """
        '#Manager.Reset':
          ResetType@Redfish.AllowableValues:
          - GracefulRestart
          target: /redfish/v1/Managers/iDRAC.Embedded.1/Actions/Manager.Reset
        """
        raise NotImplementedError()

    async def ResetToDefaults(self):
        """
        '#Manager.ResetToDefaults':
          ResetType@Redfish.AllowableValues:
          - ResetAll
          - PreserveNetworkAndUsers
          target: /redfish/v1/Managers/iDRAC.Embedded.1/Actions/Manager.ResetToDefaults

        """
        raise NotImplementedError()
