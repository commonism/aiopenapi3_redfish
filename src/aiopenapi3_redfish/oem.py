import collections

import routes
import yarl

from .odata import ResourceType


def Detour(*patterns):
    def decorator(f):
        p = "_detour"
        if (m := getattr(f, p, None)) is None:
            m = set()
            setattr(f, p, m)
        m.update(frozenset(patterns))
        return f

    return decorator


def splitTypeDetour(type_: str):
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
    detour: []

    def __init__(self):
        self._action_routes = routes.Mapper()
        self._context_map = collections.defaultdict(lambda: dict())
        for i in self.detour:
            m: str
            detour = getattr(i, "_detour")
            for m in detour:
                if m[0] == "#":
                    base, path = splitTypeDetour(m)
                    self._context_map[base][path] = i
                else:
                    self._action_routes.connect(m, cls=i)

    def classFromResourceType(self, odata_type_: str, path: str):
        t = ResourceType(odata_type_)
        for v in t.versioned, t.unversioned:
            try:
                r = self._context_map[v][path]
                return r
            except KeyError:
                continue
        return None

    def classFromRoute(self, url: str):
        assert isinstance(url, str), f"{url} {type(url)}"
        r = self._action_routes.routematch(url)
        if r is None:
            return None
        parameters, route, *_ = r
        return parameters["cls"]


class Oem(Lookup):
    pass


import aiopenapi3_redfish.actions


class Defaults(Lookup):
    detour = [aiopenapi3_redfish.actions.Actions, aiopenapi3_redfish.actions.Oem]


class Mapping:
    def __init__(self, oem=None, defaults=None):
        self._oem = oem
        self._defaults = defaults

    def classFromResourceType(self, odata_type_: str, path: str):
        for i in self._oem, self._defaults:
            if (v := i.classFromResourceType(odata_type_, path)) is not None:
                return v
        return None

    def classFromRoute(self, url: str):
        for i in self._oem, self._defaults:
            if (v := i.classFromRoute(url)) is not None:
                return v
        return None
