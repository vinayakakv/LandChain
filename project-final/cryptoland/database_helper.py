from pymongo import MongoClient


class DatabaseHelper:
    def __init__(self, url):
        self.client = MongoClient(url)

    def get_user_details(self, public_key):
        try:
            db = self.client.bigchain
            result = db.assets.find_one({
                'data.key': public_key,
                'data.type': 'REGISTER_USER',
                'data.user_type': 'USER'
            }, {"_id": 0, 'data.name': 1})
            if not result:
                raise Exception("Can not find user. Maybe key is wrong or key is not a type of USER")
            return {"success": True, "data": result['data']}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_surveyor_details(self, public_key):
        try:
            db = self.client.bigchain
            pipeline = [
                {
                    '$match': {
                        'operation': 'CREATE'
                    }
                }, {
                    '$project': {
                        '_id': 0,
                        'id': 1,
                        'inputs': 1,
                        'outputs': 1
                    }
                }, {
                    '$lookup': {
                        'from': 'assets',
                        'localField': 'id',
                        'foreignField': 'id',
                        'as': 'asset'
                    }
                }, {
                    '$match': {
                        'asset.data.type': 'SURVEY',
                        'inputs.owners_before': public_key
                    }
                }, {
                    '$unwind': {
                        'path': '$outputs',
                        'preserveNullAndEmptyArrays': False
                    }
                }, {
                    '$group': {
                        '_id': None,
                        'count': {
                            '$sum': 1
                        },
                        'totalAcre': {
                            '$sum': {
                                '$divide': [
                                    {
                                        '$toDouble': '$outputs.amount'
                                    }, 40468.6
                                ]
                            }
                        }
                    }
                }
            ]
            result = list(db.transactions.aggregate(pipeline))
            if not result:
                raise Exception(
                    "Surveyor details can not be found. Maybe key is wrong or key is not a type of SURVEYOR")
            result = result[0]
            del result['_id']
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_survey(self, survey_number):
        db = self.client.bigchain
        return db.assets.find_one({"data.type": "SURVEY", "data.surveyNumber": survey_number}, {"_id": 0})

    def get_land_transactions(self, transaction_ids: list):
        try:
            db = self.client.bigchain
            pipeline = [
                {
                    '$match': {
                        'id': {
                            '$in': transaction_ids
                        }
                    }
                }, {
                    '$lookup': {
                        'from': 'metadata',
                        'localField': 'id',
                        'foreignField': 'id',
                        'as': 'metadata'
                    }
                }, {
                    '$lookup': {
                        'from': 'assets',
                        'localField': 'asset.id',
                        'foreignField': 'id',
                        'as': 'asset'
                    }
                }, {
                    '$lookup': {
                        'from': 'assets',
                        'localField': 'id',
                        'foreignField': 'id',
                        'as': 'asset_create'
                    }
                }, {
                    '$unwind': {
                        'path': '$asset',
                        'preserveNullAndEmptyArrays': True
                    }
                }, {
                    '$unwind': {
                        'path': '$asset_create',
                        'preserveNullAndEmptyArrays': True
                    }
                }, {
                    '$unwind': {
                        'path': '$metadata',
                        'preserveNullAndEmptyArrays': True
                    }
                }, {
                    '$project': {
                        'asset': [
                            '$asset_create.data', '$asset.data'
                        ],
                        'metadata': '$metadata.metadata.divisions',
                        'txid': '$id',
                        'outputs': '$outputs.public_keys'
                    }
                }, {
                    '$unwind': {
                        'path': '$asset',
                        'preserveNullAndEmptyArrays': False
                    }
                }, {
                    '$match': {
                        'asset': {
                            '$ne': None
                        },
                        'asset.type': 'SURVEY'
                    }
                }
            ]
            result = list(db.transactions.aggregate(pipeline))
            return result
        except:
            return []

    def get_subpart_number(self, asset_id):
        try:
            db = self.client.bigchain
            pipeline = [
                {
                    '$match': {
                        'id': asset_id
                    }
                }, {
                    '$lookup': {
                        'from': 'transactions',
                        'localField': 'id',
                        'foreignField': 'asset.id',
                        'as': 'transactions'
                    }
                }, {
                    '$lookup': {
                        'from': 'metadata',
                        'localField': 'transactions.id',
                        'foreignField': 'id',
                        'as': 'metadata'
                    }
                }, {
                    '$project': {
                        'from_subpart': '$metadata.metadata.divisions.from_data.subpart_number',
                        'to_subpart': '$metadata.metadata.divisions.to_data.subpart_number'
                    }
                }, {
                    '$project': {
                        'subpart_number': {
                            '$max': [
                                {
                                    '$max': '$from_subpart'
                                }, {
                                    '$max': '$to_subpart'
                                }
                            ]
                        }
                    }
                }
            ]
            result = list(db.transactions.aggregate(pipeline))
            subpart_number = result[0]['subpart_number'] if result else 0
            subpart_number = subpart_number if subpart_number else 0
            return subpart_number + 1
        except Exception as e:
            raise e

    def get_user_asset(self, public_key):
        db = self.client.bigchain
        return db.assets.find_one({
            "data.type": {"$in": ["REGISTER_USER", "CREATE_USER"]},
            "data.key": public_key
        })

    def retrieve_assets(self, asset_type):
        db = self.client.bigchain
        return list(db.assets.find({"data.type": asset_type}, {"_id": 0}))

    def find_asset(self, key, value):
        db = self.client.bigchain
        return list(db.assets.find({key: value}, {"_id": 0}))

    def get_transfer_requests(self):
        try:
            db = self.client.bigchain
            pipeline = [
                {
                    '$match': {
                        'data.type': 'TRANSFER_REQUEST'
                    }
                }, {
                    '$lookup': {
                        'from': 'assets',
                        'localField': 'data.asset',
                        'foreignField': 'id',
                        'as': 'asset'
                    }
                }, {
                    '$unwind': {
                        'path': '$asset',
                        'preserveNullAndEmptyArrays': False
                    }
                }
            ]
            results = list(db.assets.aggregate(pipeline))
            return results
        except Exception:
            return []
