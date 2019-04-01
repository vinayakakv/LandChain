import json

from bigchaindb_driver.crypto import CryptoKeypair

from cryptoland.database_helper import DatabaseHelper
from cryptoland.transaction_helper import TransactionHelper
from .user_config import GOVERNMENT_PUBKEY, UserConfig


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


class LandTransactions:
    def __init__(self, user_config: UserConfig, database_helper: DatabaseHelper):
        self.user = user_config
        self.databaseHelper = database_helper
        self.transactionHelper = TransactionHelper("http://bigchaindb:9984")

    def get_user_assets(self):
        data = self.transactionHelper.find_asset("SURVEY")
        results = []
        for asset in data:
            transaction_id = asset['id']
            asset = asset['data']
            asset['transaction_id'] = transaction_id
            results.append(asset)
        return results

    def transfer_land(self, survey_number, divisions, transaction_id):
        user_type = self.user.get_user_type()
        user = self.user.user
        from_data = divisions['from_data']
        to_data = divisions['to_data']
        to_pubkey = self.databaseHelper.get_user_details(to_data['public_key'])
        if not user_type:
            return {"success": False, "message": "User not initialized"}
        if not to_pubkey:
            return {"success": False, "message": "Destination key doesn't correspond to a valid USER"}
        if user_type == "SURVEYOR":
            return {"success": False, "message": "SURVEYOR doesn't have the privilege to transfer land"}
        survey = self.databaseHelper.get_survey(survey_number)
        if not survey:
            return {"success": False, "message": "Could not fetch survey"}
        try:
            last_transaction = self.transactionHelper.get_transaction(transaction_id)
            if last_transaction['operation'] == "CREATE":
                asset_id = last_transaction['id']
            else:
                asset_id = last_transaction['asset']['id']
            output_index = from_data['output_index']
            metadata = {
                'asset_id': asset_id,
                'boundaries': [from_data['boundaries'], to_data['boundaries']]
            }
            if user_type == "GOVERNMENT":
                recipients = [([GOVERNMENT_PUBKEY], from_data['area']),
                              ([GOVERNMENT_PUBKEY, to_data['public_key']], to_data['area'])]
                self.transactionHelper.transfer_asset(
                    last_transaction,
                    asset_id,
                    CryptoKeypair(private_key=user['priv.key'],
                                  public_key=user['pub.key']),
                    recipients,
                    output_index,
                    metadata
                )
                return {"success": True, "data": {"status": "done"}}
            else:
                recipients = [([GOVERNMENT_PUBKEY, user['pub.key']], from_data['area']),
                              ([GOVERNMENT_PUBKEY, to_data['public_key']], to_data['area'])]
                self.transactionHelper.transfer_asset_partial_approval(
                    last_transaction,
                    asset_id,
                    CryptoKeypair(private_key=user['priv.key'],
                                  public_key=user['pub.key']),
                    GOVERNMENT_PUBKEY,
                    recipients,
                    output_index,
                    metadata
                )
                return {"success": True, "data": {"status": "waiting"}}
        except Exception as e:
            raise e
            # return {"success": False, "message": "Exception: " + str(e)}
