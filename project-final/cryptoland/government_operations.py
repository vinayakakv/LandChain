from bigchaindb_driver.crypto import CryptoKeypair

from .user_config import UserConfig
from bigchaindb_driver.exceptions import MissingPrivateKeyError


class GovernmentOperations:
    def __init__(self, user: UserConfig):
        self.config = user

    def get_user_requests(self):
        if self.config.get_user_type() != "GOVERNMENT":
            return {"success": False, "message": "Only Government user retrieve user requests"}
        assets = self.config.transactionHelper.find_asset("CREATE_USER")
        result = []
        for asset in assets:
            similar = self.config.transactionHelper.find_asset(asset['data']['key'])
            if len(similar) == 1:
                result.append(asset)
        return {"success": True, "data": result}

    def register_user(self, public_key, user_type):
        if self.config.get_user_type() != "GOVERNMENT":
            return {"success": False, "message": "Only Government user can register user"}
        registered_users = [x['data']['key'] for x in self.config.get_registered_users()['data']]
        if public_key in registered_users:
            return {"success": False, "message": "User already registered"}
        government = CryptoKeypair(public_key=self.config.user['pub.key'], private_key=self.config.user['priv.key'])
        user_requests = self.config.transactionHelper.find_asset(public_key)
        if user_requests and user_requests[-1]['data']['type'] != "CREATE_USER":
            return {"success": False, "message": "Invalid user creation request"}
        try:
            result = self.config.transactionHelper.create_asset(government, {
                'data': {
                    'type': "REGISTER_USER",
                    'key': public_key,
                    'name': user_requests[-1]['data']['name'],
                    'user_type': user_type
                }
            })
            return {"success": True, "data": result}
        except MissingPrivateKeyError:
            return {"success": False, "message": "Benami Government User!"}
