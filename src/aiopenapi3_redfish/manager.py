from typing import List
from .base import Entity, Collection, Actions


class Managers(Entity):
    class Manager_(Entity, Actions):
        pass

    def __init__(self, client: "Client", odata_id_: str):
        Entity.__init__(self, client, odata_id_)
        self.Managers: List["Managers.Manager_"] = list()

    @classmethod
    async def _init(cls, client: "Client", odata_id_: str):
        obj = await super()._init(client, odata_id_)
        obj.Managers = await Collection[Managers.Manager_]()._init(client, obj._v.odata_id_)
        return obj
