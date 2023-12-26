class ResourceType:
    def __init__(self, value):
        self.ResourceType, *version, self.TermName = value.split(".")
        self.Version = version[0] if version else ""

    @property
    def unversioned(self):
        return f"{self.ResourceType}..{self.TermName}"

    @property
    def versioned(self):
        return f"{self.ResourceType}.{self.Version}.{self.TermName}"
