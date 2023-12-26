import typing
from typing import Dict

import yarl

from pydantic import BaseModel

import aiopenapi3.model

from aiopenapi3_redfish.oem import Oem

if typing.TYPE_CHECKING:
    from .client import Client


class ResourceItem:
    def __init__(self, root: "ResourceRoot", path: yarl.URL, value: "BaseModel"):
        self._root: "ResourceRoot" = root
        self._path: yarl.URL = path
        self._v: BaseModel = value

    def __getattr__(self, name):
        try:
            v = getattr(self._v, name)
        except AttributeError:
            raise AttributeError(name)
        except RecursionError:
            pass
        if isinstance(v, (BaseModel, dict, list)):
            path = "/"
            root = self._root
            if isinstance(v, BaseModel) and "odata_type_" in v.model_fields:
                odata_type = v.odata_type_
            elif isinstance(v, dict) and "@odata.type" in v:
                odata_type = v["@odata.type"]
            else:
                path = self._path / name
                odata_type = root._v.odata_type_
            if (cls := self._root._client._oem.classFromResourceType(odata_type, str(path))) is not None:
                return cls(root, path, v)
            else:
                if isinstance(v, BaseModel):
                    return ResourceItem(root, path, v)
        return v

    def __repr__(self):
        return f"{self.__class__.__name__} {self._root} {self._path}"


class ResourceRoot(ResourceItem):
    def __init__(self, client: "Client", value: "BaseModel"):
        self._client: "Client" = client
        super().__init__(self, yarl.URL("/"), value)

    async def delete(self):
        return await self._client.delete(self._v.odata_id_)

    @classmethod
    async def _init(cls, client: "Client", odata_id_: str):
        value = await client.get(odata_id_)

        tcls = client._oem.classFromResourceType(value.odata_type_, "/")
        rcls = client._oem.classFromRoute(odata_id_)
        if rcls and tcls:
            assert tcls == rcls

        if cls == ResourceRoot or cls == ResourceItem:
            cls = tcls or rcls or cls
        return cls(client, value)

    def __repr__(self):
        return f"{self.__class__.__name__} {self._v!r}"


T = typing.TypeVar("T")


class Collection(typing.Generic[T], ResourceRoot):
    def __init__(self, client=None, data=None):
        super().__init__(client, data)
        self._data = data or {}
        self._T = None

    @property
    def T(self):
        if self._T is None:
            self._T = typing.get_args(self.__orig_class__)[0]
        return self._T

    async def _init(self, client: "Client", odata_id_: str):
        value = await client.get(odata_id_)
        super().__init__(client, value)
        self._data = self._v.Members
        return self

    async def first(self) -> T:
        i = self._data[0]
        v = await self.T._init(self._client, i.odata_id_)
        return v

    async def list(self) -> typing.Generator:
        for i in self._data:
            v = await self.T._init(self._client, i.odata_id_)
            yield v

    async def index(self, key):
        return await self.T._init(self._client, f"{self._v.odata_id_}/{key}")


class Actions:
    class Action(ResourceRoot):
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
            type_ = self._client._oem.classFromRoute(v["target"])
            cls = type_(self._client, v["target"])
            r[k] = cls
        return r
