from pathlib import Path
import collections
from pathlib import Path
import collections


import aiopenapi3.plugin
from aiopenapi3.json import JSONReference

from .base import _DocumentBase


class Document_vX(_DocumentBase):
    """
    Generate Version anyOf …
    """

    def __init__(self, url, directory):
        super().__init__(url)
        self.dir = directory

    def removeInvalidVersions(self, ctx: aiopenapi3.plugin.Document.Context) -> None:
        r: dict[str, list[str]] = collections.defaultdict(list)
        for name, value in ctx.document["components"]["schemas"].items():
            if "anyOf" not in value:
                continue

            def fileExists(x):
                return (self.dir / "OpenAPI" / Path(JSONReference.split(x["$ref"])[0]).name).exists()

            new = list(filter(fileExists, value["anyOf"]))

            # if (a:=set(JSONReference.split(i["$ref"])[0] for i in new)) != (b:=set(JSONReference.split(i["$ref"])[0] for i in value["anyOf"])):
            #    print(f"{ctx.url}#{name} ({sorted(b - a)})")
            #            if (a := set(JSONReference.split(i["$ref"])[0] for i in new)) != (b := set(JSONReference.split(i["$ref"])[0] for i in value["anyOf"])):
            #                print(f"{ctx.url}#{name} {sorted(a)}")

            for i in new:
                name, _, version = (Path(JSONReference.split(i["$ref"])[0])).stem.partition(".v")
                if name == "odata-v4":
                    continue
                if version not in r[name]:
                    r[name].append(version)

            value["anyOf"] = new

        for name, versions in sorted(r.items(), key=lambda x: x[0]):
            n = tuple([name, tuple(versions)])
            print(n)

    def parsed(self, ctx: aiopenapi3.plugin.Document.Context) -> aiopenapi3.plugin.Document.Context:
        super().parsed(ctx)
        if ctx.url != self._url:
            path = Path(ctx.url.path)
            if "." not in path.stem:
                self.removeInvalidVersions(ctx)

        self.fixDellManager(ctx)
        self.fixResourceHealth(ctx)
        self.fixTaskService(ctx)
        return ctx
