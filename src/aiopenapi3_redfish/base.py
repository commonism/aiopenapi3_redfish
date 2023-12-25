import typing
from typing import Dict

import yarl

import aiopenapi3.model

if typing.TYPE_CHECKING:
    from .client import Client
    from pydantic import BaseModel


class Entity:
    def __init__(self, client: "Client", value: "BaseModel"):
        self._client: "Client" = client
        self._v: "BaseModel" = value

    def __getattr__(self, name):
        try:
            return getattr(self._v, name)
        except AttributeError:
            raise AttributeError(name)

    async def delete(self):
        return await self._client.delete(self._v.odata_id_)

    @classmethod
    async def _init(cls, client: "Client", odata_id_: str):
        value = await client.get(odata_id_)
        return cls(client, value)

    def __repr__(self):
        return f"{self.__class__.__name__} {self._v!r}"


T = typing.TypeVar("T")


class Collection(typing.Generic[T], Entity):
    def __init__(self):
        pass

    async def _init(self, client: "Client", odata_id_: str):
        value = await client.get(odata_id_)
        super().__init__(client, value)
        self._T = typing.get_args(self.__orig_class__)[0]
        return self

    async def first(self) -> T:
        i = self._v.Members[0]
        v = await self._T._init(self._client, i.odata_id_)
        return v

    async def list(self) -> typing.Generator:
        for i in self._v.Members:
            v = await self._T._init(self._client, i.odata_id_)
            yield v

    async def index(self, key):
        return await self._T._init(self._client, f"{self._v.odata_id_}/{key}")


class Actions:
    class Action(Entity):
        def __init__(self, client: "Client", odata_id_: str, title, fields):
            super().__init__(client, odata_id_)
            self.title = title
            self.fields: Dict[str, str] = fields

        async def __call__(self, *args, **kwargs):
            req = self._client.api.createRequest((self.odata_id_, "post"))
            r = await req(*args, **kwargs)
            return r

    def __getitem__(self, key):
        name = aiopenapi3.model.Model.nameof(key)
        v = getattr(self._v.Actions, name)
        return Actions.Action(self._client, v.target, v.title, v.model_extra)

    @property
    def Oem(self) -> "Actions":
        r = dict()
        for k, v in self._v.Actions.Oem.model_extra.items():
            url = yarl.URL(v["target"])
            parameters, url = self._client._oem.routeOf(url)
            cls = parameters["cls"](self._client, url)
            r[k] = cls
        return r
