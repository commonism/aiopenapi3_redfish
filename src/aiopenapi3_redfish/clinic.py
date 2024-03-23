import collections
import json
import inspect

import aiopenapi3.v31
import yaml
import aiopenapi3.plugin
import aiopenapi3_redfish


class RedfishDocument(aiopenapi3.plugin.Document):
    def __init__(self, url):
        self._url = url
        super().__init__()

    def parsed(self, ctx: "aiopenapi3.plugin.Document.Context") -> "aiopenapi3.plugin.Document.Context":
        base = yaml.safe_load(
            f"""
            openapi: 3.1.0

            info:
              description: This contains the definition of a Redfish service.
              title: Redfish for '{ctx.url}'
              version: '2022.1'

            paths: {{}}
            """
        )
        base.update(ctx.document)
        ctx.document = base

        if str(ctx.url) == self._url:
            """
            this is the openapi.yaml description document with the PathItems
            """
            root = yaml.safe_load(
                """
                servers:
                    - url: /

                security:
                  - basicAuth: []
                  - X-Auth: []
                """
            )

            root.update(ctx.document)
            root["components"].update(
                yaml.safe_load(
                    """
                securitySchemes:
                  basicAuth:
                    type: http
                    scheme: basic

                  X-Auth:
                    in: header
                    name: X-Auth-Token
                    type: apiKey
                """
                )
            )

            ctx.document = root

        if "title" in ctx.document:
            del ctx.document["title"]


class NullableRefs(aiopenapi3.plugin.Document):
    """
    The DMTF OpenAPI reference description documents incorrectly use nullable on references in properties and arrays
    In OpenAPI 3.0 nullable is not a valid property on References and gets ignored, therefore the affected models
    do not accept None values. This causes problems when rejecting messages which are are valid by the intention of the
    specification but invalid due to the improper specification of nullable values.

    This plugin modifies the parsed description documents, It removes nullable from the reference and modifies/replaces
    it with a definition matching the intention of the specification.

    This problem in present in DSP8010 and not fixed yet (as of version 2023.3/17 Jan 2024)
    FIXME https://github.com/DMTF/Redfish-Tools/issues/464
    """

    @classmethod
    def fixschema(cls, s):
        if s.get("type", "object") == "object" and "properties" in s:
            for pn, p in list(s["properties"].items()):
                if "nullable" in p and "$ref" in p:
                    ref = p["$ref"]
                    del p["nullable"]
                    del p["$ref"]
                    s["properties"][pn] = {
                        **p,
                        "oneOf": [{"$ref": ref}, {"enum": ["null"]}],
                    }
                else:
                    cls.fixschema(p)
        elif s.get("type", "array") == "array" and "items" in s:
            if "nullable" in (items := s["items"]) and "$ref" in items:
                del s["items"]["nullable"]
                s["nullable"] = True

    def parsed(self, ctx: "Document.Context") -> "Document.Context":
        for name, s in ctx.document["components"]["schemas"].items():
            self.fixschema(s)

        return ctx


from aiopenapi3.base import HTTP_METHODS


class ExposeResponseHeaders(aiopenapi3.plugin.Init):
    def paths(self, ctx: "aiopenapi3.plugin.Init.Context") -> "aiopenapi3.plugin.Init.Context":
        # all return Location
        for p, pi in ctx.paths.paths.items():
            for m in HTTP_METHODS:
                if (op := getattr(pi, m, None)) is None:
                    continue
                for status_code, response in op.responses.items():
                    response.headers = {
                        "Location": aiopenapi3.v31.parameter.Header(
                            required=False, schema=aiopenapi3.v31.schemas.Schema(type="string")
                        )
                    }

                    # SessionService X-Auth-Token
                    if p == "/redfish/v1/SessionService/Sessions" and m == "post":
                        response.headers["X-Auth-Token"] = aiopenapi3.v31.parameter.Header(
                            required=False, schema=aiopenapi3.v31.schemas.Schema(type="string")
                        )
        return ctx


from aiopenapi3.base import SchemaBase
from typing import Iterable


class PayloadAnnotations(aiopenapi3.plugin.Init):
    def __init__(self):
        super().__init__()

    def _annotate(self, schemas: Iterable[SchemaBase]):
        for schema in schemas:
            if not isinstance(schema, SchemaBase):
                continue
            if schema.extensions is None or (pp := schema.extensions.get("patternProperties", None)) is None:
                continue
            schema.patternProperties = dict()
            for ppattern, _ in pp.items():
                schema.patternProperties[ppattern] = dict()

    def resolved(self, ctx: "Init.Context") -> "Init.Context":
        self._annotate(ctx.resolved)
        return ctx


def Received(*patterns, method=None):
    return _Routes("_received", *patterns, method=method)


def Parsed(*patterns, method=None):
    return _Routes("_parsed", *patterns, method=method)


def _Routes(_route, *patterns, method=None):
    def x(f):
        setattr(f, _route, (m := getattr(f, _route, set())))
        m.update(frozenset((p, tuple(method) if method else None) for p in patterns))
        return f

    return x


class Message(aiopenapi3.plugin.Message):
    class Methods:
        def __init__(self):
            self._get = self._post = self._patch = self._put = self._delete = None
            self.default = None

        @property
        def get(self):
            return self._get or self.default

        @property
        def post(self):
            return self._post or self.default

        @property
        def patch(self):
            return self._patch or self.default

        @property
        def put(self):
            return self._put or self.default

        @property
        def delete(self):
            return self._delete or self.default

    def __init__(self):
        super().__init__()
        self._received = collections.defaultdict(lambda: Message.Methods())
        self._parsed = collections.defaultdict(lambda: Message.Methods())
        for op, mapping in {"_received": self._received, "_parsed": self._parsed}.items():
            for name, i in filter(
                lambda kv: kv[1] and inspect.ismethod(kv[1]) and hasattr(kv[1], op),
                map(lambda x: (x, getattr(self, x)), dir(self)),
            ):
                objmap = getattr(i, op)
                for url, methods in objmap:
                    if methods:
                        for m in methods:
                            setattr(mapping[url], f"_{m}", i)
                    else:
                        mapping[url].default = i

    def _dr(self, what, ctx):
        if (r := what.get(ctx.request.path, None)) and (m := getattr(r, ctx.request.method, None)):
            m(ctx)
        return ctx

    def parsed(self, ctx: "aiopenapi3.plugin.Message.Context") -> "aiopenapi3.plugin.Message.Context":
        return self._dr(self._parsed, ctx)

    def received(self, ctx: "aiopenapi3.plugin.Message.Context") -> "aiopenapi3.plugin.Message.Context":
        """
        7.5 Data modification requests

        status_code 202 data modification requests do not return a Task as required by the spec but only a url to the
        Task in the Location header
        As the plugin interface is not async, we can not retrieve the actual Task and are limited create a Task limited
        to the TaskId to work with
        """
        match ctx.request.method, ctx.status_code:
            case ["post" | "put" | "patch", "202"]:
                """
                DSP0266 - 7.5.2 Modification success responses
                """
                location = ctx.headers["Location"]
                _, _, jobid = location.rpartition("/")
                ctx.received = json.dumps(
                    {
                        "@odata.id": location,
                        "@odata.type": "#Task._.Task",
                        "Id": jobid,
                        "Name": "",
                    }
                )
        return self._dr(self._received, ctx)
