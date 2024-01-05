from typing import Dict, Optional

import aiopenapi3.model

from .base import ResourceItem
from .oem import Detour


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


@Detour("#CertificateService..CertificateService/Actions")
@Detour("#EventService..EventService/Actions")
@Detour("#Manager..Manager/Actions")
@Detour("#TelemetryService..TelemetryService/Actions")
@Detour("#UpdateService..UpdateService/Actions")
class Actions(ResourceItem):
    _detour = None

    def __new__(cls, *args, **kwargs):
        cls.__detour = set()
        return super().__new__(cls)

    def __getitem__(self, key):
        name = aiopenapi3.model.Model.nameof(key)
        v = getattr(self._v, name)
        return self._createAction(v.target, v.title, v.model_extra)

    def _createAction(self, target, title, fields):
        parameters, url = self._root._client.routeOf(target)
        type_ = self._root._client._mapping.classFromRoute(target) or Action
        r = type_(self._root._client, url, parameters, target, title, fields)
        return r


@Detour("#CertificateService..CertificateService/Actions/Oem")
@Detour("#EventService..EventService/Actions/Oem")
@Detour("#Manager..Manager/Actions/Oem")
@Detour("#TelemetryService..TelemetryService/Actions/Oem")
@Detour("#UpdateService..UpdateService/Actions/Oem")
class Oem(Actions):
    _detour = None

    def __getitem__(self, key):
        v = self._v.model_extra[key]
        return self._createAction(v["target"], v.get("title", None), v)
