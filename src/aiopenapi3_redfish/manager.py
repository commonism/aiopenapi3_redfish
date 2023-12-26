from typing import List

import yarl

from .base import ResourceRoot, Collection, Actions


class Managers(ResourceRoot):
    class Manager_(ResourceRoot, Actions):
        pass

    def __init__(self, client: "Client", odata_id_: str):
        ResourceRoot.__init__(self, client, odata_id_)
        self.Managers: List["Managers.Manager_"] = list()

    @classmethod
    async def _init(cls, client: "Client", odata_id_: str):
        obj = await super()._init(client, odata_id_)
        obj.Managers = await Collection[Managers.Manager_]()._init(client, obj._v.odata_id_)
        return obj
