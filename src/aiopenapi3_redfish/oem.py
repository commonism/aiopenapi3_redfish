import routes
import yarl


def Routes(*patterns):
    def decorator(f):
        p = "_match"
        setattr(f, p, (m := getattr(f, p, set())))
        m.update(frozenset(patterns))
        return f

    return decorator


class Oem:
    def __init__(self):
        self.routes = routes.Mapper()

    def connect(self, routes):
        for i in routes:
            for m in i._match:
                self.routes.connect(m.replace("#", "%23"), cls=i)

    def routeOf(self, url: yarl.URL):
        assert isinstance(url, yarl.URL), f"{url} {type(url)}"
        r = self.routes.routematch(str(url.with_fragment(None)))
        if r is None:
            raise KeyError(url)
        parameters, route, *_ = r
        return parameters, route.routepath
