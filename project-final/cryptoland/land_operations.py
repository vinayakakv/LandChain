import json

from bigchaindb_driver.crypto import CryptoKeypair

from cryptoland.database_helper import DatabaseHelper
from cryptoland.transaction_helper import TransactionHelper
from .user_config import GOVERNMENT_PUBKEY


class Survey:
    def __init__(self, request, user_config):
        self.user = user_config
        self.transactionHelper = TransactionHelper("http://bigchaindb:9984")
        request = json.loads(request)
        self.surveyNumber = request['surveyNumber']
        self.landType = request['landType']
        self.boundaries = json.loads(request['boundaries'])
        self.id = self.boundaries["id"]
        self.area = int(request["area"])
        self.type = "SURVEY"
        self.save()

    def __str__(self):
        dictionary = {
            "surveyNumber": self.surveyNumber,
            "boundaries": self.boundaries,
            "landType": self.landType,
            "id": self.id,
            "type": self.type
        }
        return json.dumps(dictionary)

    def save(self):
        asset = {
            'data': {
                "surveyNumber": self.surveyNumber,
                "boundaries": self.boundaries,
                "landType": self.landType,
                "id": self.id,
                "type": self.type
            }
        }
        current_user = self.user.user
        keypair = CryptoKeypair(public_key=current_user['pub.key'],
                                private_key=current_user['priv.key'])
        print(asset, keypair)
        self.transactionHelper.create_divisible_asset(
            creator=keypair,
            owner_pubkey=GOVERNMENT_PUBKEY,
            asset=asset,
            quantity=self.area
        )

    @staticmethod
    def get_surveys():
        transactionHelper = TransactionHelper("http://bigchaindb:9984")
        data = transactionHelper.find_asset("SURVEY")
        results = []
        for asset in data:
            asset = asset['data']
            results.append(asset)
        return results
