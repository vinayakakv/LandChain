import rapidjson

import base58
from cryptoconditions import ThresholdSha256, Ed25519Sha256
from sha3 import sha3_256

from bigchaindb_driver import BigchainDB
import bigchaindb_driver as driver


class TransactionHelper:
    def __init__(self, ip):
        self.driver = BigchainDB(ip)

    def create_asset(self, owner, asset, recipients=None):
        if recipients is None:
            recipients = (owner.public_key,)
        prepared_tx = self.driver.transactions.prepare(
            operation='CREATE',
            signers=owner.public_key,
            asset=asset,
            recipients=recipients
        )
        fulfilled_tx = self.driver.transactions.fulfill(
            prepared_tx,
            private_keys=owner.private_key
        )
        return self.driver.transactions.send_commit(fulfilled_tx)

    def create_divisible_asset(self, creator, owner_pubkey, asset, quantity):
        prepared_tx = self.driver.transactions.prepare(
            operation='CREATE',
            signers=creator.public_key,
            recipients=[([owner_pubkey], quantity)],
            asset=asset
        )
        fulfilled_tx = self.driver.transactions.fulfill(
            prepared_tx, private_keys=creator.private_key
        )
        return self.driver.transactions.send_commit(fulfilled_tx)

    def transfer_asset(self, last_transaction, asset_id, owner, to, output_index=0, metadata=None):
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
        prepared_tx = self.driver.transactions.prepare(
            operation='TRANSFER',
            asset=transfer_asset,
            inputs=transfer_input,
            recipients=to,
            metadata=metadata
        )
        fulfilled_tx = self.driver.transactions.fulfill(
            prepared_tx,
            private_keys=owner.private_key,
        )
        return self.driver.transactions.send_commit(fulfilled_tx)

    def transfer_asset_partial_approval(self, last_transaction, asset_id, owner1, owner2_pubkey, to, output_index=0,
                                        metadata=None):
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
        prepared_tx = self.driver.transactions.prepare(
            operation='TRANSFER',
            asset=transfer_asset,
            inputs=transfer_input,
            recipients=to,
            metadata=metadata
        )
        prepared_tx['inputs'][0]['fulfillment'] = None
        message = rapidjson.dumps(prepared_tx, skipkeys=False, ensure_ascii=False,
                                  sort_keys=True)
        message = sha3_256(message.encode())
        message.update('{}{}'.format(
            prepared_tx['inputs'][0]['fulfills']['transaction_id'],
            prepared_tx['inputs'][0]['fulfills']['output_index']).encode()
                       )
        threshold_sha256 = ThresholdSha256(threshold=2)
        owner1_ed25519 = Ed25519Sha256(public_key=base58.b58decode(owner1.public_key))
        owner1_ed25519.sign(message=message.digest(),
                            private_key=base58.b58decode(owner1.private_key))
        threshold_sha256.add_subfulfillment(owner1_ed25519)
        # Now create a new asset in the name of owner 2
        payload = threshold_sha256.to_dict()
        asset = {
            'data': {
                'type': 'TRANSFER_REQUEST',
                'message': rapidjson.dumps(prepared_tx),
                'fulfillment': rapidjson.dumps(payload)
            }
        }
        return self.create_asset(owner1, asset, (owner2_pubkey,))

    def complete_partial_transfer(self, transfer_asset, owner2):
        payload = rapidjson.loads(transfer_asset['data']['fulfillment'])
        prepared_transfer_tx = rapidjson.loads(transfer_asset['data']['message'])
        message = rapidjson.dumps(prepared_transfer_tx, skipkeys=False, ensure_ascii=False,
                                  sort_keys=True)
        threshold_sha256 = ThresholdSha256().from_dict(payload)
        message = sha3_256(message.encode())
        message.update('{}{}'.format(
            prepared_transfer_tx['inputs'][0]['fulfills']['transaction_id'],
            prepared_transfer_tx['inputs'][0]['fulfills']['output_index']).encode()
                       )
        government_ed25519 = Ed25519Sha256(public_key=base58.b58decode(owner2.public_key))
        government_ed25519.sign(message=message.digest(),
                                private_key=base58.b58decode(owner2.private_key))
        threshold_sha256.add_subfulfillment(government_ed25519)
        fulfillment_uri = threshold_sha256.serialize_uri()
        prepared_transfer_tx['inputs'][0]['fulfillment'] = fulfillment_uri
        json_str_tx = rapidjson.dumps(prepared_transfer_tx, skipkeys=False, ensure_ascii=False,
                                      sort_keys=True)
        txid = sha3_256(json_str_tx.encode()).hexdigest()
        prepared_transfer_tx['id'] = txid
        driver.common.transaction.Transaction.validate_id(prepared_transfer_tx)
        return self.driver.transactions.send_commit(prepared_transfer_tx)

    def find_transactions(self, asset_id):
        return self.driver.transactions.get(asset_id=asset_id)

    def get_transaction(self, transaction_id):
        return self.driver.transactions.retrieve(transaction_id)

    def get_unspent_outputs(self, public_key):
        return self.driver.outputs.get(public_key, spent=False)
