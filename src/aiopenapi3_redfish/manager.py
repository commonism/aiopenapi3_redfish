from typing import List

import yarl

from .base import AsyncResourceRoot, AsyncCollection


class Managers(AsyncResourceRoot):
    class Manager_(AsyncResourceRoot):
        pass

    def __init__(self, client: "Client", odata_id_: str):
        AsyncResourceRoot.__init__(self, client, odata_id_)
        self.Managers: List["Managers.Manager_"] = list()

    @classmethod
    async def asyncInit(cls, client: "Client", odata_id_: str):
        obj = await super().asyncInit(client, odata_id_)
        obj.Managers = await AsyncCollection[Managers.Manager_]().asyncInit(client, obj._v.odata_id_)
        return obj
