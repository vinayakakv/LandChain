import json


class Survey:
    def __init__(self, request):
        # self.raw_data = request
        request = json.loads(request)
        self.surveyNumber = request['surveyNumber']
        self.landType = request['landType']
        self.boundaries = json.loads(request['boundaries'])
        self.id = self.boundaries["id"]
        self.save()

    def __str__(self):
        return json.dumps(self.__dict__)

    def save(self):
        with open("surveys.txt", "a")as f:
            f.write(str(self) + "\n")

    @staticmethod
    def get_surveys():
        try:
            with open("surveys.txt", "r+") as f:
                return [json.loads(x) for x in f.readlines() if x != " "]
        except IOError:
            return []
