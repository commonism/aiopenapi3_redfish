import typing
from typing import Dict, Optional

import yarl

from pydantic import BaseModel

import aiopenapi3.model

from aiopenapi3_redfish.errors import RedfishException
from aiopenapi3_redfish.oem import Oem

if typing.TYPE_CHECKING:
    from .client import AsyncClient


class ResourceItem:
    def __init__(self, root: "AsyncResourceRoot", path: yarl.URL, value: "BaseModel"):
        self._root: "AsyncResourceRoot" = root
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


class AsyncResourceRoot(ResourceItem):
    def __init__(self, client: "AsyncClient", value: "BaseModel"):
        self._client: "AsyncClient" = client
        super().__init__(self, yarl.URL("/"), value)

    async def get(self, *args, **kwargs):
        return await self._client.get(self._v.odata_id_, *args, **kwargs)

    async def patch(self, *args, **kwargs):
        return await self._client.patch(self._v.odata_id_, *args, context=self, **kwargs)

    async def delete(self):
        return await self._client.delete(self._v.odata_id_, context=self)

    @classmethod
    async def asyncInit(cls, client: "AsyncClient", odata_id_: str):
        value = await client.get(odata_id_)

        tcls = client._oem.classFromResourceType(value.odata_type_, "/")
        rcls = client._oem.classFromRoute(odata_id_)
        if rcls and tcls:
            assert tcls == rcls

        if cls == AsyncResourceRoot or cls == ResourceItem:
            cls = tcls or rcls or cls
        return cls(client, value)

    def __repr__(self):
        return f"{self.__class__.__name__} {self._v!r}"


T = typing.TypeVar("T")


class AsyncCollection(typing.Generic[T], AsyncResourceRoot):
    def __init__(self, client=None, data=None):
        super().__init__(client, data)
        self._data = data or {}
        self._T = None

    @property
    def T(self):
        if self._T is None:
            self._T = typing.get_args(self.__orig_class__)[0]
        return self._T

    async def asyncInit(self, client: "AsyncClient", odata_id_: str):
        value = await client.get(odata_id_)
        super().__init__(client, value)
        self._data = self._v.Members
        return self

    async def first(self) -> T:
        i = self._data[0]
        v = await self.T.asyncInit(self._client, i.odata_id_)
        return v

    async def refresh(self):
        self._v = await self._client.get(self._v.odata_id_)
        self._data = self._v.Members
        return self

    async def list(self, skip_errors=True) -> typing.Generator:
        for i in self._data:
            try:
                v = await self.T.asyncInit(self._client, i.odata_id_)
                yield v
            except RedfishException as e:
                if skip_errors:
                    continue
                raise e

    async def index(self, key):
        return await self.T.asyncInit(self._client, f"{self._v.odata_id_}/{key}")


class AsyncActions:
    class Action:
        def __init__(self, client: "AsyncClient", url: str, parameters: Dict[str, str], odata_id_: str, title, fields):
            self._client = client
            self.odata_id_ = odata_id_
            self.title = title
            self.fields: Dict[str, str] = fields
            self.parameters = parameters
            self.url = url
            self.req = self._client.api.createRequest((self.url, "post"))

        @property
        def data(self):
            return self.req.data.get_type()

        async def __call__(self, *args, parameters: Optional[Dict[str, str]] = None, **kwargs):
            if parameters:
                parameters.update(self.parameters)
            else:
                parameters = self.parameters
            r = await self.req(*args, parameters=parameters, **kwargs)
            return r

    def __getitem__(self, key):
        name = aiopenapi3.model.Model.nameof(key)
        v = getattr(self._v.Actions, name)
        return self._createAction(v.target, v.title, v.model_extra)

    def _createAction(self, target, title, fields):
        parameters, url = self._client.routeOf(target)
        type_ = self._client._oem.classFromRoute(target) or AsyncActions.Action
        r = type_(self._client, url, parameters, target, title, fields)
        return r

    @property
    def Oem(self) -> "AsyncActions":
        r = dict()
        for k, v in self._v.Actions.Oem.model_extra.items():
            try:
                cls = self._createAction(v["target"], v.get("title", ""), v)
            except KeyError:
                print(f"missing {v['target']}")
                continue
            r[k] = cls
        return r
