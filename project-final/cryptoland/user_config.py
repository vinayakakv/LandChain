from bigchaindb_driver import BigchainDB
from bigchaindb_driver.crypto import generate_keypair
import pathlib


class TransactionHelper:
    def __init__(self):
        self.driver = BigchainDB("http://bigchaindb:9984")

    def create_user_asset(self, owner, user_name):
        user_asset = {
            'data': {
                'type': "CREATE_USER",
                'key': owner.public_key,
                'name': user_name
            }
        }
        prepared_creation_tx = self.driver.transactions.prepare(
            operation='CREATE',
            signers=owner.public_key,
            asset=user_asset,
        )
        fulfilled_creation_tx = self.driver.transactions.fulfill(
            prepared_creation_tx,
            private_keys=owner.private_key
        )
        sent_creation_tx = self.driver.transactions.send_commit(fulfilled_creation_tx)
        return sent_creation_tx

    def find_asset(self, key):
        return self.driver.assets.get(search=key)

    def find_transactions(self, asset_id):
        return self.driver.transactions.get(asset_id=asset_id)


# To be done
GOVERNMENT_PUBKEY = ""


class UserConfig:
    def __init__(self):
        self.transactionHelper = TransactionHelper()
        self.keydir = pathlib.Path("/keys")
        self.users = {}
        for file in self.keydir.glob('*key'):
            if file.is_file():
                self.users[file.name] = open(file, 'r').readlines()[0].rstrip()
        keys = self.users.keys()
        if keys:
            if 'pub.key' not in keys:
                self.users['pub.key'] = GOVERNMENT_PUBKEY
            self.users['name'] = self.get_user_name()
            self.users['user_type'] = self.get_user_type()

    def create_user(self, user_name):
        if self.users.keys():
            return {"success": False, "message": "User exists"}
        user = generate_keypair()
        self.users = {
            'pub.key': user.public_key,
            'priv.key': user.private_key,
            'name': user_name,
            'user_type': None
        }
        with open(self.keydir / 'pub.key', 'w') as f:
            f.write(user.public_key)
        with open(self.keydir / 'priv.key', 'w') as f:
            f.write(user.private_key)
        result = self.transactionHelper.create_user_asset(user, user_name)
        return {"success": True, "data": result}

    def get_system_user(self):
        self.__init__()
        return {k: self.users[k] for k in self.users if k != "priv.key"}

    def get_user_name(self):
        user_asset = self.transactionHelper.find_asset(self.users['pub.key'])[0]
        return user_asset['data']['name']

    def get_registered_users(self):
        return self.transactionHelper.find_asset("REGISTER_USER")

    def get_user_type(self):
        user_assets = self.transactionHelper.find_asset(self.users['pub.key'])
        user_type = None
        for user_asset in user_assets:
            if user_asset['data']['type'] == "REGISTER_USER":
                transactions = self.transactionHelper.find_transactions(user_asset['id'])[-1]
                if GOVERNMENT_PUBKEY in transactions['outputs'][0]['public_keys']:
                    user_type = user_asset['data']['user_type']
        return user_type
