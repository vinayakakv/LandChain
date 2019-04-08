import pathlib

from bigchaindb_driver.crypto import generate_keypair, CryptoKeypair
from bigchaindb_driver.exceptions import MissingPrivateKeyError

from cryptoland.database_helper import DatabaseHelper
from cryptoland.transaction_helper import TransactionHelper

GOVERNMENT_PUBKEY = pathlib.Path("app/cryptoland/government.key").read_text().rstrip()
BURN_PUBKEY = "BurnBurnBurnBurnBurnBurnBurnBurnBurnBurnBurn"


class UserConfig:
    def __init__(self):
        self.transactionHelper = TransactionHelper("http://bigchaindb:9984")
        self.databaseHelper = DatabaseHelper("mongodb://bigchaindb:27017")
        self.keydir = pathlib.Path("/keys")
        self.user = {}
        for file in self.keydir.glob('*key'):
            if file.is_file():
                self.user[file.name] = open(file, 'r').readlines()[0].rstrip()
        keys = self.user.keys()
        if keys:
            if 'pub.key' not in keys:
                self.user = {}
                return
            self.user['name'] = self.get_user_name()
            if self.user['name'] is None:
                self.user = {}
                return
            self.user['user_type'] = self.get_user_type()

    def create_user(self, user_name):
        if self.user.keys():
            return {"success": False, "message": "User exists"}
        user = generate_keypair()
        self.user = {
            'pub.key': user.public_key,
            'priv.key': user.private_key,
            'name': user_name,
            'user_type': None
        }
        with open(self.keydir / 'pub.key', 'w') as f:
            f.write(user.public_key)
        with open(self.keydir / 'priv.key', 'w') as f:
            f.write(user.private_key)
        try:
            result = self.transactionHelper.create_asset(user, {
                'data': {
                    'type': "CREATE_USER",
                    'key': user.public_key,
                    'name': user_name
                }
            })
            return {"success": True, "data": result}
        except MissingPrivateKeyError:
            return {"success": False, "message": "Invalid User"}

    def get_system_user(self):
        if not self.user.get('user_type', None):
            self.__init__()
        return {k: self.user[k] for k in self.user if k != "priv.key"}

    def get_user_name(self):
        user_asset = self.databaseHelper.get_user_asset(self.user['pub.key'])
        if user_asset:
            return user_asset['data']['name']
        else:
            return None

    def get_user_type(self):
        if self.user == {}:
            return None
        user_type = self.user.get('user_type', None)
        if user_type is not None:
            return user_type
        user_assets = self.databaseHelper.find_asset("data.key", self.user['pub.key'])
        to_burn = False
        burn_id = None
        for user_asset in user_assets:
            if user_asset['data']['type'] == "REGISTER_USER":
                transactions = self.transactionHelper.find_transactions(user_asset['id'])[-1]
                if GOVERNMENT_PUBKEY in transactions['outputs'][0]['public_keys']:
                    user_type = user_asset['data']['user_type']
                    to_burn = True
            if user_asset['data']['type'] == "CREATE_USER":
                burn_id = user_asset['id']
        if to_burn and burn_id:
            transactions = self.transactionHelper.find_transactions(burn_id)
            if len(transactions) == 1:  # not burnt yet
                transaction = transactions[0]
                self.transactionHelper.transfer_asset(
                    transaction,
                    burn_id,
                    CryptoKeypair(public_key=self.user['pub.key'],
                                  private_key=self.user['priv.key']),
                    BURN_PUBKEY
                )

        return user_type

    def get_registered_users(self):
        return {"success": True, "data": self.databaseHelper.retrieve_assets("REGISTER_USER")}
