import copy

from .base import Entity, Collection, Actions


class AccountService(Entity):
    class ManagerAccount(Entity):
        pass

    def __init__(self, client: "Client", odata_id_: str):
        Entity.__init__(self, client, odata_id_)
        self.Accounts: "AccountService._Accounts" = None

    @classmethod
    async def _init(cls, client: "Client", odata_id_: str):
        obj = await super()._init(client, odata_id_)
        obj.Accounts = await Collection[AccountService.ManagerAccount]()._init(client, obj._v.Accounts.odata_id_)
        return obj


class CertificateService(Entity, Actions):
    pass


class Chassis(Entity):
    pass


class EventService(Entity):
    pass


class Fabrics(Entity):
    pass


class JobService(Entity):
    pass


class LicenseService(Entity):
    pass


class SessionService(Entity):
    class Session(Entity):
        pass

    async def createSession(self):
        auth = copy.copy(self._client.api._security["basicAuth"])
        req = self._client.api._[("/redfish/v1/SessionService/Sessions", "post")]
        data = req.data.get_type().model_validate(
            {"@odata.id": "", "@odata.type": "", "Id": "", "Name": "", "UserName": auth[0], "Password": auth[1]}
        )
        #        r = await req(data=data.model_dump(exclude_unset=True))

        data = {"UserName": auth[0], "Password": auth[1]}
        try:
            self._client.api.authenticate(None)
            headers, value = await req(data=data, return_headers=True)
            self._client.api.authenticate(**{"X-Auth": headers["X-Auth-Token"]})
            self._session = (headers, value)
        except KeyError:
            self._client.api.authenticate(None)
            self._client.api.authenticate(basicAuth=auth)
            return False
        return True

    @classmethod
    async def _init(cls, client: "Client", odata_id_: str):
        obj = await super()._init(client, odata_id_)
        obj.Sessions = await Collection[SessionService.Session]()._init(client, obj._v.Sessions.odata_id_)
        return obj


class Systems(Entity):
    pass


class TaskService(Entity, Actions):
    pass


class TelemetryService(Entity, Actions):
    pass


class UpdateService(Entity, Actions):
    pass
