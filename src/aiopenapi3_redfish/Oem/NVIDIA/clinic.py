import aiopenapi3_redfish.clinic


class Message(aiopenapi3_redfish.clinic.Message):
    @aiopenapi3_redfish.clinic.Parsed("/redfish/v1/AccountService/Accounts/{ManagerAccountId}", method=["get"])
    def dr_ManagerAccount(self, ctx: "aiopenapi3_redfish.clinic.Message.Context"):
        ctx.parsed["AccountTypes"] = []
        return ctx
