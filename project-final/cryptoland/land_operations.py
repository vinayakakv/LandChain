import json
from collections import defaultdict

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
            "type": self.type,
            "area": self.area
        }
        return json.dumps(dictionary)

    def save(self):
        asset = {
            'data': {
                "surveyNumber": self.surveyNumber,
                "boundaries": json.dumps(self.boundaries),
                "landType": self.landType,
                "id": self.id,
                "type": self.type,
                "area": self.area
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
        databaseHelper = DatabaseHelper("mongodb://bigchaindb:27017")
        data = databaseHelper.retrieve_assets("SURVEY")
        results = []
        for asset in data:
            asset = asset['data']
            asset['boundaries'] = json.loads(asset['boundaries'])
            results.append(asset)
        return results


class LandTransactions:
    def __init__(self, user_config: UserConfig, database_helper: DatabaseHelper):
        self.user = user_config
        self.databaseHelper = database_helper
        self.transactionHelper = TransactionHelper("http://bigchaindb:9984")

    def get_user_assets(self):
        public_key = self.user.get_system_user()['pub.key']
        utxos = self.transactionHelper.get_unspent_outputs(public_key)
        data = defaultdict(list)
        for utxo in utxos:
            data[utxo['transaction_id']].append(utxo['output_index'])
        transactions = self.databaseHelper.get_land_transactions(list(data.keys()))
        results = []
        for transaction in transactions:
            output_indices = data[transaction['txid']]
            for output_index in output_indices:
                result = {**transaction['asset'],
                          'type': 'partial' if len(transaction['outputs'][output_index]) > 1 else 'full'}
                if 'metadata' in transaction:
                    metadata = transaction['metadata']
                    metadata = [metadata['from_data'], metadata['to_data']]
                    for datum in metadata:
                        if datum['public_key'] == public_key:
                            result['boundaries'] = json.loads(datum['boundaries'])
                            result['area'] = datum['area']
                            if result['area'] > 0:
                                subpart_number = datum.get('subpart_number', 0)
                                result['surveyNumber'] += '/' + str(subpart_number) if subpart_number != 0 else ""
                else:
                    result['boundaries'] = json.loads(result['boundaries'])
                result['transaction_id'] = transaction['txid']
                result['output_index'] = output_index
                results.append(result)
        return results

    def transfer_land(self, survey_number, transaction_id, output_index, to_public_key, divisions):
        user_type = self.user.get_user_type()
        user = self.user.user
        to_details = self.databaseHelper.get_user_details(to_public_key)
        if not user_type:
            return {"success": False, "message": "User not initialized"}
        if not to_details:
            return {"success": False, "message": "Destination key doesn't correspond to a valid USER"}
        if user_type == "SURVEYOR":
            return {"success": False, "message": "SURVEYOR don't have the privilege to transfer land"}
        split = survey_number.split('/')
        subpart_number = split[1] if len(split) > 1 else 0
        survey_number = split[0]
        survey = self.databaseHelper.get_survey(survey_number)
        if not survey:
            return {"success": False, "message": "Could not fetch survey"}
        try:
            last_transaction = self.transactionHelper.get_transaction(transaction_id)
            if last_transaction['operation'] == "CREATE":
                asset_id = last_transaction['id']
            else:
                asset_id = last_transaction['asset']['id']
            divisions['from_data']['public_key'] = user['pub.key']
            divisions['to_data']['public_key'] = to_public_key
            metadata = {
                'asset_id': asset_id,
                'divisions': divisions
            }
            from_area = divisions['from_data']['area']
            if from_area > 0:
                metadata['divisions']['from_data']['subpart_number'] = int(subpart_number)
                metadata['divisions']['to_data']['subpart_number'] = self.databaseHelper.get_subpart_number(asset_id)
            to_area = divisions['to_data']['area']
            if user_type == "GOVERNMENT":
                recipients = []
                if from_area > 0:
                    recipients.append(([GOVERNMENT_PUBKEY], from_area))
                recipients.append(([GOVERNMENT_PUBKEY, to_public_key], to_area))
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
                recipients = []
                if from_area > 0:
                    recipients.append(([GOVERNMENT_PUBKEY, user['pub.key']], from_area))
                recipients.append(([GOVERNMENT_PUBKEY, to_public_key], to_area))
                if user['pub.key'] == to_public_key:
                    raise Exception("Can not transfer the asset to same user")
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
            return {"success": False, "message": "Exception: " + repr(e)}
