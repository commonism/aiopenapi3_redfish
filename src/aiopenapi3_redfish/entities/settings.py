from aiopenapi3_redfish.base import AsyncResourceRoot
from aiopenapi3_redfish.oem import Detour


class AsyncSettings(AsyncResourceRoot):
    """
    9.10 Settings resource
    """

    async def set(self, **values):
        odata_id_ = (
            self._v.model_extra.get("@Redfish.Settings", {})
            .get("SettingsObject", {})
            .get("@odata.id", self._v.odata_id_)
        )
        return await self._client.patch(odata_id_, values, self._v)


@Detour("#Bios..Bios")
class AsyncBios(AsyncSettings):
    pass
