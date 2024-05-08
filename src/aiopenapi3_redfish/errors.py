import typing

if typing.TYPE_CHECKING:
    import pydantic


class RedfishException(Exception):
    def __init__(self, value: "pydantic.BaseModel"):
        self.value = value
