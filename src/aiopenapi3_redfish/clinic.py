import aiopenapi3.v31
import yaml

from aiopenapi3.plugin import Init, Document, Message

import aiopenapi3_redfish


class RedfishDocument(Document):
    def __init__(self, url):
        self._url = url
        super().__init__()

    def parsed(self, ctx: "Document.Context") -> "Document.Context":
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


from aiopenapi3.base import HTTP_METHODS


class ExposeResponseHeaders(Init):
    def paths(self, ctx: "Init.Context") -> "Init.Context":
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


class PayloadAnnotations(Init):
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
