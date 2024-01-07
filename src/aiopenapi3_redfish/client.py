import typing
from typing import List, Union
from pathlib import Path

import httpx
import yarl
import routes

from aiopenapi3 import OpenAPI
from aiopenapi3.loader import ChainLoader

from aiopenapi3_redfish.errors import RedfishException
from aiopenapi3_redfish.oem import Oem

from .serviceroot import AsyncServiceRoot

if typing.TYPE_CHECKING:
    from .service import (
        AsyncAccountService,
        AsyncUpdateService,
        AsyncTelemetryService,
        AsyncCertificateService,
        AsyncSessionService,
        AsyncEventService,
        AsyncTaskService,
    )
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


class AsyncClient:
    def __init__(self, config):
        self.config = config
        self.api = self.createAPI(config)
        self._serviceroot: AsyncServiceRoot = None

        self.routes = routes.Mapper()
        for i in self.api.paths.paths.keys():
            self.routes.connect(i)

        self._mapping: "Mapping" = None
        self._RedfishError = self.api.components.schemas["RedfishError"].get_type()

    async def asyncInit(self):
        self._serviceroot = await AsyncServiceRoot.asyncInit(self, "/redfish/v1")

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

    async def delete(self, path, context=None):
        return await self._request(path, "delete", context=context)

    async def get(self, path):
        return await self._request(path, "get")

    async def patch(self, path, data, context):
        return await self._request(path, "patch", data=data, context=context)

    async def _request(self, path, method, parameters=None, data=None, context=None):
        p, routepath = self.routeOf(yarl.URL(path))
        req = self.api._[(routepath, method)]
        if parameters is not None:
            p.update(parameters)
        r = await req(parameters=p, data=data, context=context)
        if isinstance(r, self._RedfishError):
            raise RedfishException(r)
        return r

    @property
    def AccountService(self) -> "AsyncAccountService":
        return self._serviceroot.AccountService

    @property
    def CertificateService(self) -> "AsyncCertificateService":
        return self._serviceroot.CertificateService

    @property
    def EventService(self) -> "AsyncEventService":
        return self._serviceroot.EventService

    @property
    def Manager(self) -> "Manager":
        return self._serviceroot.Manager

    @property
    def SessionService(self) -> "AsyncSessionService":
        return self._serviceroot.SessionService

    @property
    def TaskService(self) -> "AsyncTaskService":
        return self._serviceroot.TaskService

    @property
    def TelemetryService(self) -> "AsyncTelemetryService":
        return self._serviceroot.TelemetryService

    @property
    def UpdateService(self) -> "AsyncUpdateService":
        return self._serviceroot.UpdateService

    @property
    def Vendor(self):
        """

        .. versionadded::   v1.5
        """
