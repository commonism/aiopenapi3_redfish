import collections

import routes
import yarl

from .odata import ResourceType


def Routes(*patterns):
    def decorator(f):
        p = "_match"
        setattr(f, p, (m := getattr(f, p, set())))
        m.update(frozenset(patterns))
        return f

    return decorator


def Context(base, path):
    def decorator(f):
        p = "_ctx"
        setattr(f, p, (m := getattr(f, p, set())))
        m.add((base, path))
        return f

    return decorator


class Oem:
    actions: []
    context: []

    def __init__(self):
        self._action_routes = routes.Mapper()
        self._context_map = collections.defaultdict(lambda: dict())
        for i in self.actions:
            m: str
            for m in i._match:
                self._action_routes.connect(m, cls=i)

        for i in self.context:
            for base, path in i._ctx:
                self._context_map[base][path] = i

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
