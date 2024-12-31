import collections
import json
import inspect
import typing
from collections.abc import Iterable
import re
from pathlib import Path
import logging

import yaml
import pydantic

from aiopenapi3.base import SchemaBase, HTTP_METHODS
import aiopenapi3.v31
import aiopenapi3.plugin

import aiopenapi3_redfish

log = logging.getLogger(__name__)


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
    def fixschema(cls, s: dict[str, str]):
        # 2024.1
        if s.get("type", None) is None and "oneOf" in s:
            try:
                s["oneOf"].remove({"enum": ["null"]})
            except ValueError:
                pass
            else:
                s["oneOf"].append({"enum": [None]})
            return

        if s.get("type", "object") == "object" and "properties" in s:
            for pn, p in list(s["properties"].items()):
                cls.fixschema(p)
        elif s.get("type", "array") == "array" and "items" in s:
            cls.fixschema(s["items"])
        elif (ref := s.get("$ref")) is not None and s.get("nullable") is True:
            del s["nullable"]
            del s["$ref"]
            if "type" in s:
                del s["type"]
            n = {
                **s,
                "oneOf": [
                    {"$ref": ref},
                    {"enum": [None]},
                ],
            }
            s.clear()
            s.update(n)

    def parsed(self, ctx: "aiopenapi3.plugin.Document.Context") -> "aiopenapi3.plugin.Document.Context":
        for name, s in ctx.document["components"]["schemas"].items():
            self.fixschema(s)

        return ctx


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

    def resolved(self, ctx: aiopenapi3.plugin.Init.Context) -> aiopenapi3.plugin.Init.Context:
        self._annotate(ctx.resolved)
        return ctx

    class TypeExpectation(aiopenapi3.plugin.Message, aiopenapi3.plugin.Init):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.schemas: collections.ChainMap[str, pydantic.BaseModel] | None = None

        def initialized(self, ctx: "Init.Context") -> "Init.Context":
            self.schemas = collections.ChainMap(*(i.components.schemas for i in self.api._documents.values()))
            return ctx

        def parsed(self, ctx: "aiopenapi3.plugin.Message.Context") -> "aiopenapi3.plugin.Message.Context":
            try:
                ctx.expected_type.model(ctx.parsed)
            except pydantic.ValidationError:
                pass
            else:
                return

            if location := ctx.parsed.get("@odata.type"):
                assert location[0] == "#"
                name, _, sub = location[1:].rpartition(".")
            elif location := ctx.headers.get("link"):
                name, _, rel = location.partition(";")
                name = name.strip("<>")
                name = Path(name).stem
            elif tuple(ctx.parsed.keys()) == ("error",):
                name = "RedfishError"
            else:
                #                print(ctx.parsed)
                return ctx

            try:
                if name == "RedfishError":
                    type_ = name
                elif "." in name:
                    """
                    Chassis.v1_6_0
                    """
                    name, _, version = name.partition(".")
                    p = re.compile(r"^{name}_v\d+_\d+_\d+_{name}$".format(name=name))
                    type_ = list(filter(lambda x: p.match(x), self.schemas.keys()))[0]
                else:
                    """
                    EventDestinationCollection
                    """
                    p = re.compile("^{name}_{name}$".format(name=name))
                    type_ = list(filter(lambda x: p.match(x), self.schemas.keys()))[0]
            except Exception as e:
                print(f"{e} {name} not found")
                return

            if (linked_type := self.schemas.get(type_)) != ctx.expected_type:
                try:
                    linked_type.model(ctx.parsed)
                    err = None
                except Exception as e:
                    err = e
                finally:
                    log.info(
                        f"type correction -> {ctx.expected_type.get_type().__name__} -> {linked_type.get_type().__name__} ({err})"
                    )
                    ctx.expected_type = linked_type
            return ctx


def Received(*patterns, method=None):
    return _Routes("_received", *patterns, method=method)


def Parsed(*patterns, method=None):
    return _Routes("_parsed", *patterns, method=method)


def Sending(*patterns, method=None):
    return _Routes("_sending", *patterns, method=method)


def _Routes(_route, *patterns, method=None):
    def x(
        f: typing.Callable[
            [aiopenapi3_redfish.clinic.Message, aiopenapi3.plugin.Message.Context], aiopenapi3.plugin.Message.Context
        ]
    ):
        m: set[tuple[str, list[HTTP_METHODS] | None]]
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
        self._received: dict[str, Message.Methods] = collections.defaultdict(lambda: Message.Methods())
        self._parsed: dict[str, Message.Methods] = collections.defaultdict(lambda: Message.Methods())
        self._sending: dict[str, Message.Methods] = collections.defaultdict(lambda: Message.Methods())
        for op, mapping in {"_received": self._received, "_parsed": self._parsed, "_sending": self._sending}.items():
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

    def sending(self, ctx: "Message.Context") -> "Message.Context":
        return self._dr(self._sending, ctx)
