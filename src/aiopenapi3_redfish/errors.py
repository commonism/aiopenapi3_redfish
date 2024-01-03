class RedfishException(Exception):
    def __init__(self, value: "pydantic.BaseModel"):
        self.value = value
