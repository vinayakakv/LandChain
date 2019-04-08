import argparse
import pathlib
import sys

from bigchaindb_driver.crypto import generate_keypair

from cryptoland.database_helper import DatabaseHelper
from cryptoland.transaction_helper import TransactionHelper

parser = argparse.ArgumentParser(description='Create Government User')
parser.add_argument("-s", '--bigchaindb-ip',
                    dest="ip",
                    help="BigchainDB REST API Server IP",
                    default='http://bigchaindb:9984')
parser.add_argument("-k", '--key-dir',
                    dest="key_dir",
                    help="Location to store the keys",
                    default="/keys")
args = parser.parse_args()
tr = TransactionHelper(args.ip)
db = DatabaseHelper("mongodb://{}:27017".format("localhost" if "localhost" in args.ip else "bigchaindb"))
if db.find_asset("data.user_type", "GOVERNMENT"):
    print("GOVERNMENT already exists in the network ... Can not create new one", file=sys.stderr)
    exit(-1)
keydir = pathlib.Path(args.key_dir)
government = generate_keypair()
print("Creating Government User with Public Key : {},  Private Key : {}".format(government.public_key,
                                                                                government.private_key))
print("Storing Public Key in {}".format(keydir / 'pub.key'))
with open(keydir / 'pub.key', 'w+') as f:
    f.write(government.public_key)
print("Storing Private Key in {}".format(keydir / 'priv.key'))
with open(keydir / 'priv.key', 'w+') as f:
    f.write(government.private_key)

print("Committing Transaction to BigchainDB...")
res = tr.create_asset(government, {
    'data': {
        'type': "REGISTER_USER",
        'key': government.public_key,
        'name': "Government",
        'user_type': "GOVERNMENT"
    }
})
print("Result is {}".format(res))
