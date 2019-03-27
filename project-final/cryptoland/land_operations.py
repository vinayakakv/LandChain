import json

from bigchaindb_driver.crypto import CryptoKeypair

from cryptoland.transaction_helper import TransactionHelper
from .user_config import UserConfig, GOVERNMENT_PUBKEY

user = UserConfig()


class Survey:
    def __init__(self, request):
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
                "boundaries": json.dumps(self.boundaries),
                "landType": self.landType,
                "id": self.id,
                "type": self.type
            }
        }
        current_user = user.user
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
            asset['boundaries'] = json.loads(asset['boundaries'])
            results.append(asset)
        return results
