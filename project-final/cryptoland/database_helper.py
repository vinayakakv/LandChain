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
                                    }, {
                                        '$multiply': [
                                            1000000000, 4046.86
                                        ]
                                    }
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
            pass
