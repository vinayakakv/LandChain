import rapidjson

from bigchaindb_driver.crypto import CryptoKeypair
from bigchaindb_driver.exceptions import MissingPrivateKeyError

from .user_config import UserConfig, BURN_PUBKEY


class GovernmentOperations:
    def __init__(self, user: UserConfig):
        self.config = user

    def get_user_requests(self):
        if self.config.get_user_type() != "GOVERNMENT":
            return {"success": False, "message": "Only Government user retrieve user requests"}
        assets = self.config.databaseHelper.retrieve_assets("CREATE_USER")
        result = []
        for asset in assets:
            similar = self.config.databaseHelper.find_asset("data.key", asset['data']['key'])
            if len(similar) == 1:
                result.append(asset)
        return {"success": True, "data": result}

    def get_transfer_requests(self):
        if self.config.get_user_type() != "GOVERNMENT":
            return {"success": False, "message": "Only Government user retrieve user requests"}
        requests = self.config.databaseHelper.get_transfer_requests()
        results = []
        for request in requests:
            similar = self.config.transactionHelper.driver.transactions.get(asset_id=request['id'])
            if len(similar) == 1:
                result = {
                    **request['asset']['data'],
                    'asset_id': request['id'],
                    'boundaries': rapidjson.loads(request['data']['metadata']['divisions']['to_data']['boundaries']),
                    'from': request['data']['from'],
                    'to': request['data']['to']
                }
                subpart_number = request['data']['metadata']['divisions']['to_data'].get('subpart_number', 0)
                result['surveyNumber'] += '/' + str(subpart_number) if subpart_number > 0 else ""
                results.append(result)
        return {"success": True, "data": results}

    def register_user(self, public_key, user_type):
        if self.config.get_user_type() != "GOVERNMENT":
            return {"success": False, "message": "Only Government user can register user"}
        registered_users = [x['data']['key'] for x in self.config.get_registered_users()['data']]
        if public_key in registered_users:
            return {"success": False, "message": "User already registered"}
        government = CryptoKeypair(public_key=self.config.user['pub.key'], private_key=self.config.user['priv.key'])
        user_requests = self.config.databaseHelper.find_asset("data.key", public_key)
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

    def resolve_request(self, asset_id, reject):
        if self.config.get_user_type() != "GOVERNMENT":
            return {"success": False, "message": "Only Government user retrieve user requests"}
        asset = self.config.databaseHelper.find_asset("id", asset_id)
        if len(asset) == 0:
            return {"success": False, "message": "Invalid asset id"}
        asset = asset[0]
        transactions = self.config.transactionHelper.driver.transactions.get(asset_id=asset_id)
        if len(transactions) != 1:
            return {"success": False, "message": "Request was already resolved"}
        government = CryptoKeypair(
            private_key=self.config.user['priv.key'],
            public_key=self.config.user['pub.key']
        )
        try:
            commit = None
            if not reject:
                commit = self.config.transactionHelper.complete_partial_transfer(
                    asset,
                    government
                )
            burn = self.config.transactionHelper.transfer_asset(
                transactions[-1],
                asset_id,
                government,
                BURN_PUBKEY
            )
            return {"success": True, "data": {"commit": commit, "burn": burn}}
        except Exception as e:
            raise e
