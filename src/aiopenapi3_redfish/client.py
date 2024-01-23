import typing
from typing import List, Union
from pathlib import Path
import logging

import httpx
import yarl
import routes

from aiopenapi3 import OpenAPI
from aiopenapi3.loader import ChainLoader

from aiopenapi3_redfish.errors import RedfishException

from aiopenapi3_redfish.base import AsyncResourceRoot


if typing.TYPE_CHECKING:
    from aiopenapi3_redfish.entities.service import (
        AsyncAccountService,
        AsyncUpdateService,
        AsyncTelemetryService,
        AsyncCertificateService,
        AsyncSessionService,
        AsyncEventService,
        AsyncTaskService,
    )
    from .serviceroot import AsyncServiceRoot
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


class AsynClientLoggingAdapter(logging.LoggerAdapter):
    """
    This example adapter expects the passed in dict-like object to have a
    'connid' key, whose value in brackets is prepended to the log message.
    """

    def process(self, msg, kwargs):
        return "[%s] %s" % (self.extra["target"], msg), kwargs


class AsyncClient:
    _log = logging.getLogger("aiopenapi3_redfish.AsyncClient")

    def __init__(self, config, api):
        self.config = config
        self.api = api
        self._serviceroot: AsyncServiceRoot = None

        self.routes = routes.Mapper()
        for i in self.api.paths.paths.keys():
            self.routes.connect(i)

        self._mapping: "Mapping" = None
        self._RedfishError = self.api.components.schemas["RedfishError"].get_type()
        self.log = AsynClientLoggingAdapter(self._log, extra=dict(target=yarl.URL(self.config.target).host))

    @classmethod
    def fromConfig(cls, config: Config, api=None) -> "AsyncClient":
        if api is None:
            api = cls.createAPI(config)
        return cls(config, api)

    async def asyncInit(self):
        self._serviceroot = await AsyncResourceRoot.asyncNew(self, "/redfish/v1")

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
        return await self._request_send(req, p, data, context)

    async def _request_send(self, req, parameters, data, context=None, **kwargs):
        r = await req(parameters=parameters, data=data, context=context, **kwargs)
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
    def Chassis(self) -> "AsyncChassis":
        return self._serviceroot.Chassis

    @property
    def EventService(self) -> "AsyncEventService":
        return self._serviceroot.EventService

    @property
    def JobService(self) -> "AsyncEventService":
        return self._serviceroot.JobService

    @property
    def Manager(self) -> "Manager":
        return self._serviceroot.Manager

    @property
    def SessionService(self) -> "AsyncSessionService":
        return self._serviceroot.SessionService

    @property
    def Systems(self) -> "Any":
        return self._serviceroot.Systems

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
