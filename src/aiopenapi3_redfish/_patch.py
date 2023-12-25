import routes


def patch_routes():
    """
    https://github.com/bbangert/routes/issues/114
    """
    import routes.route
    import re

    def Route_buildfullreg(self, clist, include_names=True):
        """Build the regexp by iterating through the routelist and
        replacing dicts with the appropriate regexp match"""
        regparts = []
        offsets = list()
        for part in self.routelist:
            if isinstance(part, dict):
                var = part["name"]
                if var == "controller":
                    partmatch = "|".join(map(re.escape, clist))
                elif part["type"] == ":":
                    partmatch = self.reqs.get(var) or "[^/]+?"
                elif part["type"] == ".":
                    partmatch = self.reqs.get(var) or "[^/.]+?"
                else:
                    partmatch = self.reqs.get(var) or ".+?"
                if include_names:
                    if var not in offsets:
                        offsets.append(var)
                        regpart = "(?P<%s>%s)" % (var, partmatch)
                    else:
                        offset = offsets.index(var)
                        regpart = f"\\{offset+1}"
                else:
                    regpart = "(?:%s)" % partmatch
                if part["type"] == ".":
                    regparts.append(r"(?:\.%s)??" % regpart)
                else:
                    regparts.append(regpart)
            else:
                regparts.append(re.escape(part))
        regexp = "".join(regparts) + "$"
        return regexp

    if not hasattr(patch_routes, "__ran__"):
        setattr(patch_routes, "__ran__", True)
        routes.route.Route.buildfullreg = Route_buildfullreg
