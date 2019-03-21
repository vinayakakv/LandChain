from bigchaindb_driver import BigchainDB
from bigchaindb_driver.crypto import generate_keypair, CryptoKeypair
import pathlib

from bigchaindb_driver.exceptions import MissingPrivateKeyError


class TransactionHelper:
    def __init__(self, ip):
        self.driver = BigchainDB(ip)

    def create_user_asset(self, owner, user_asset):
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

    def transfer_asset(self, last_transaction, asset_id, owner, to):
        output_index = 0
        output = last_transaction['outputs'][output_index]
        transfer_input = {
            'fulfillment': output['condition']['details'],
            'fulfills': {
                'output_index': output_index,
                'transaction_id': last_transaction['id'],
            },
            'owners_before': output['public_keys']
        }
        transfer_asset = {
            'id': asset_id
        }
        prepared_transfer_tx = self.driver.transactions.prepare(
            operation='TRANSFER',
            asset=transfer_asset,
            inputs=transfer_input,
            recipients=to,
        )
        fulfilled_transfer_tx = self.driver.transactions.fulfill(
            prepared_transfer_tx,
            private_keys=owner.private_key,
        )
        return self.driver.transactions.send_commit(fulfilled_transfer_tx)

    def find_asset(self, key):
        return self.driver.assets.get(search=key)

    def find_transactions(self, asset_id):
        return self.driver.transactions.get(asset_id=asset_id)


GOVERNMENT_PUBKEY = "7t2SxbSo7tRKm7FhsEfTnUgWvKaYKvMTYNeAALcNs4Bk"
BURN_PUBKEY = "BurnBurnBurnBurnBurnBurnBurnBurnBurnBurnBurn"


class UserConfig:
    def __init__(self):
        self.transactionHelper = TransactionHelper("http://bigchaindb:9984")
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
            result = self.transactionHelper.create_user_asset(user, {
                'data': {
                    'type': "CREATE_USER",
                    'key': user.public_key,
                    'name': user_name
                }
            })
            return {"success": True, "data": result}
        except MissingPrivateKeyError:
            return {"success": False, "message": "Invalid User"}

    def register_user(self, public_key, user_type):
        if self.get_user_type() != "GOVERNMENT":
            return {"success": False, "message": "Only Government user can register user"}
        registered_users = [x['data']['key'] for x in self.get_registered_users()['data']]
        if public_key in registered_users:
            return {"success": False, "message": "User already registered"}
        government = CryptoKeypair(public_key=self.user['pub.key'], private_key=self.user['priv.key'])
        user_requests = self.transactionHelper.find_asset(public_key)
        if user_requests and user_requests[-1]['data']['type'] != "CREATE_USER":
            return {"success": False, "message": "Invalid user creation request"}
        try:
            result = self.transactionHelper.create_user_asset(government, {
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

    def get_system_user(self):
        self.__init__()
        return {k: self.user[k] for k in self.user if k != "priv.key"}

    def get_user_name(self):
        user_asset = self.transactionHelper.find_asset(self.user['pub.key'])[0]
        return user_asset['data']['name']

    def get_registered_users(self):
        if self.get_user_type() != "GOVERNMENT":
            return {"success": False, "message": "Only Government user retrieve register user"}
        return {"success": True, "data": self.transactionHelper.find_asset("REGISTER_USER")}

    def get_user_requests(self):
        if self.get_user_type() != "GOVERNMENT":
            return {"success": False, "message": "Only Government user retrieve user requests"}
        assets = self.transactionHelper.find_asset("CREATE_USER")
        result = []
        for asset in assets:
            transactions = self.transactionHelper.find_transactions(asset['id'])
            if transactions[-1]['operation'] == "CREATE":
                result.append(asset)
        return {"success": True, "data": result}

    def get_user_type(self):
        if self.user == {}:
            return None
        user_assets = self.transactionHelper.find_asset(self.user['pub.key'])
        user_type = None
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
