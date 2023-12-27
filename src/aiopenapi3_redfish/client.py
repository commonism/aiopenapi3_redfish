import typing
from typing import List, Union
from pathlib import Path

import httpx
import yarl
import routes

from aiopenapi3 import OpenAPI
from aiopenapi3.loader import ChainLoader

from aiopenapi3_redfish.oem import Oem

from .service import (
    AccountService,
    UpdateService,
    TelemetryService,
    CertificateService,
    SessionService,
    EventService,
    TaskService,
)
from .manager import Managers

if typing.TYPE_CHECKING:
    from aiopenapi3.plugin import Plugin
    from aiopenapi3.loader import Loader


class Config:
    def __init__(
        self,
        target: str,
        username: str,
        password: str,
        cache: Path = None,
        plugins: List["Plugin"] = None,
        locations: List["Loader"] = None,
        session_factory: Union[httpx.AsyncClient | httpx.Client] = httpx.AsyncClient,
    ):
        self.target: str = target
        self.auth = (username, password)
        self.cache: Path = cache
        self.plugins: List["Plugin"] = plugins or []
        self.locations: List["Loader"] = locations or []
        self.session_factory: Union[httpx.AsyncClient | httpx.Client] = session_factory


class Client:
    def __init__(self, config):
        self.config = config
        self.api = self.createAPI(config)
        self._serviceroot: "ServiceRoot" = None
        self._accountservice: "AccountService" = None

        self.routes = routes.Mapper()
        for i in self.api.paths.paths.keys():
            self.routes.connect(i)

        self._oem: Oem = None

    async def ainit(self):
        self._serviceroot = await self.get("/redfish/v1")
        self._accountservice = await AccountService._init(self, self._serviceroot.AccountService.odata_id_)
        self._certificateservice = await CertificateService._init(self, self._serviceroot.CertificateService.odata_id_)
        self._eventservice = await EventService._init(self, self._serviceroot.EventService.odata_id_)
        self._updateservice = await UpdateService._init(self, self._serviceroot.UpdateService.odata_id_)
        self._telemetryservice = await TelemetryService._init(self, self._serviceroot.TelemetryService.odata_id_)
        self._managers = await Managers._init(self, self._serviceroot.Managers.odata_id_)
        self._manager = await self._managers.Managers.first()
        self._sessionservice = await SessionService._init(self, self._serviceroot.SessionService.odata_id_)
        self._taskservice = await TaskService._init(self, self._serviceroot.Tasks.odata_id_)

    @classmethod
    def createAPI(cls, config):
        api = None
        if config.cache and config.cache.exists():
            api = OpenAPI.cache_load(config.cache, config.plugins, config.session_factory)
            api._base_url = yarl.URL(config.target)
        else:
            loader = ChainLoader(*config.locations)
            api = OpenAPI.load_file(
                config.target,
                yarl.URL("openapi.yaml"),
                loader=loader,
                plugins=config.plugins,
                session_factory=config.session_factory,
            )
            if config.cache:
                api.cache_store(config.cache)

        api._session_factory = config.session_factory
        api.authenticate(basicAuth=config.auth)
        return api

    def routeOf(self, url: Union[str, yarl.URL]):
        if isinstance(url, yarl.URL):
            url = str(url.with_fragment(None))
        r = self.routes.routematch(url)
        if r is None:
            raise KeyError(url)
        parameters, route, *_ = r
        return parameters, route.routepath

    async def delete(self, path):
        return await self._request(path, "delete")

    async def get(self, path):
        return await self._request(path, "get")

    async def _request(self, path, method):
        parameters, routepath = self.routeOf(yarl.URL(path))
        req = self.api._[(routepath, method)]
        r = await req(parameters=parameters)
        return r

    @property
    def AccountService(self) -> "AccountService":
        return self._accountservice

    @property
    def CertificateService(self) -> "CertificateService":
        return self._certificateservice

    @property
    def EventService(self) -> "EventService":
        return self._eventservice

    @property
    def Manager(self) -> "Manager":
        return self._manager

    @property
    def SessionService(self) -> "SessionService":
        return self._sessionservice

    @property
    def TaskService(self) -> "TaskService":
        return self._taskservice

    @property
    def TelemetryService(self) -> "UpdateService":
        return self._telemetryservice

    @property
    def UpdateService(self) -> "UpdateService":
        return self._updateservice

    @property
    def Vendor(self):
        """

        .. versionadded::   v1.5
        """
