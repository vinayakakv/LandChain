from bigchaindb_driver import BigchainDB


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

    def transfer_asset(self, last_transaction, asset_id, owner, to, output_index=0):
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
        )
        fulfilled_tx = self.driver.transactions.fulfill(
            prepared_tx,
            private_keys=owner.private_key,
        )
        return self.driver.transactions.send_commit(fulfilled_tx)

    def find_asset(self, key):
        return self.driver.assets.get(search=key)

    def find_transactions(self, asset_id):
        return self.driver.transactions.get(asset_id=asset_id)
