import collections
import typing
from typing import Optional, Union
import routes

from .odata import ResourceType


if typing.TYPE_CHECKING:
    from .base import ResourceItem
    from .entities.actions import Action

    ResourceItemType: typing.TypeAlias = typing.Type[ResourceItem]
    ActionType: typing.TypeAlias = typing.Type[Action]
    DetourType: typing.TypeAlias = ResourceItemType | ActionType


def Detour(*patterns: str) -> typing.Callable[["DetourType"], "DetourType"]:
    def decorator(f):
        p = "_detour"
        if (m := getattr(f, p, None)) is None:
            m = set()
            setattr(f, p, m)
        m.update(frozenset(patterns))
        return f

    return decorator


def splitTypeDetour(type_: str) -> tuple[str, str]:
    """

    :param type_: #name.version.name/path
    :return: (#name.version.name, '/{path}')
    """
    try:
        i = type_.index("/")
        base = type_[:i]
        path = type_[i:]
    except ValueError:
        base = type_
        path = "/"
    return base, path


class Lookup:
    detour: list["DetourType"] = []

    def __init__(self):
        self._action_routes = routes.Mapper()
        self._context_map: dict[str, dict[str, "DetourType"]] = collections.defaultdict(lambda: dict())
        for i in self.detour:
            m: str
            detour = getattr(i, "_detour")
            for m in detour:
                if m[0] == "#":
                    base, path = splitTypeDetour(m)
                    self._context_map[base][path] = i
                else:
                    self._action_routes.connect(m, cls=i)

    def classFromResourceType(
        self, odata_type_: str, path: str | None
    ) -> Optional[Union["DetourType", dict[str, "DetourType"]]]:
        t = ResourceType(odata_type_)
        for v in t.versioned, t.unversioned:
            try:
                r: "DetourType" | dict[str, "DetourType"]
                if v in self._context_map:
                    if path is not None:
                        r = self._context_map[v][path]
                    else:
                        r = self._context_map[v]
                    return r
                else:
                    raise KeyError(v)
            except KeyError:
                continue
        return None

    def classFromRoute(self, url: str) -> Optional["ResourceItem"]:
        assert isinstance(url, str), f"{url} {type(url)}"
        r = self._action_routes.routematch(url)
        if r is None:
            return None
        parameters, route, *_ = r
        return parameters["cls"]


class Oem(Lookup):
    pass


class Mapping:
    def __init__(self, oem=None, defaults=None):
        self._oem = oem
        self._defaults = defaults

    def classFromResourceType(self, odata_type_: str, path: str | None):
        r = dict()
        for i in self._oem, self._defaults:
            if (v := i.classFromResourceType(odata_type_, path)) is not None:
                if path:
                    return v
                r.update(v)
        if path or not r:
            return None
        return r

    def classFromRoute(self, url: str):
        for i in self._oem, self._defaults:
            if (v := i.classFromRoute(url)) is not None:
                return v
        return None
