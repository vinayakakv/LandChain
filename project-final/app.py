import rapidjson

from flask import Flask, render_template, send_from_directory, request, jsonify, abort

from cryptoland.government_operations import GovernmentOperations
from cryptoland.land_operations import Survey, LandTransactions
from cryptoland.user_config import UserConfig
from cryptoland.database_helper import DatabaseHelper

app = Flask(__name__, static_url_path='')
user = UserConfig()
government = GovernmentOperations(user)
database_helper = DatabaseHelper('mongodb://bigchaindb:27017/')
land_transactions = LandTransactions(user, database_helper)


@app.route('/<string:role>/<path:path>')
def send_file(role, path):
    if role == "guest":
        return render_template(path)
    elif role.upper() == user.get_user_type():
        return send_from_directory('templates/', role + '/' + path)
    else:
        abort(401)


@app.route('/home')
def serve_home():
    user_type = user.get_user_type()
    if not user_type:
        abort(401)
    return send_from_directory('templates/', user_type.lower() + '/home.html')


@app.route('/about')
def serve_about():
    return send_from_directory('templates/', 'about.html')


@app.route('/survey')
def serve_survey():
    if user.get_user_type() == "SURVEYOR":
        return send_from_directory('templates/', 'surveyor/survey.html')
    else:
        abort(401)


@app.route('/register')
def serve_register():
    if user.get_user_type() == "GOVERNMENT":
        return send_from_directory('templates/', 'government/register.html')
    else:
        abort(401)


@app.route('/distribute')
def serve_distribute():
    if user.get_user_type() == "GOVERNMENT":
        return send_from_directory('templates/', 'government/distribute.html')
    else:
        abort(401)


@app.route('/view')
def serve_view():
    if user.get_user_type() == "GOVERNMENT":
        return send_from_directory('templates/', 'government/view.html')
    else:
        abort(401)


@app.route('/resolve')
def serve_resolve():
    if user.get_user_type() == "GOVERNMENT":
        return send_from_directory('templates/', 'government/resolve.html')
    else:
        abort(401)


@app.route('/transact')
def serve_transact():
    if user.get_user_type() == "USER":
        return send_from_directory('templates/', 'user/transact.html')
    else:
        abort(401)


@app.route('/history')
def serve_history():
    return send_from_directory('templates/', 'history.html')


@app.route('/saveSurvey', methods=['POST'])
def save_survey():
    if user.get_user_type() != "SURVEYOR":
        return jsonify({"success": False, "message": "Only Surveyor can survey"})
    s = Survey(request.data, user)
    return jsonify({"success": True, "data": rapidjson.loads(str(s))})


@app.route('/getSurveys', methods=['POST', 'GET'])
def get_surveys():
    return jsonify({"success": True, "data": Survey.get_surveys()})


@app.route('/getAssetHistory', methods=['POST'])
def get_asset_history():
    req = rapidjson.loads(request.data)
    survey_number = req['survey_number'].strip()
    return jsonify(database_helper.get_asset_history(survey_number))


@app.route('/getSystemUser', methods=['POST', 'GET'])
def get_system_user():
    return jsonify({"success": True, "data": user.get_system_user()})


@app.route('/addSystemUser', methods=['POST', 'GET'])
def add_system_user():
    req = rapidjson.loads(request.data)
    user_name = req['user_name']
    return jsonify(user.create_user(user_name))


@app.route('/registerUser', methods=['POST'])
def register_user():
    req = rapidjson.loads(request.data)
    public_key = req['public_key'].strip()
    user_type = req['user_type'].strip().upper()
    return jsonify(government.register_user(public_key, user_type))


@app.route('/resolveRequest', methods=['POST'])
def resolve_request():
    req = rapidjson.loads(request.data)
    asset_id = req['asset_id'].strip()
    reject = req['reject']
    return jsonify(government.resolve_request(asset_id, reject))


@app.route('/getRegisteredUsers', methods=['POST', 'GET'])
def get_registered_users():
    return jsonify(user.get_registered_users())


@app.route('/getUserRequests', methods=['POST', 'GET'])
def get_user_requests():
    return jsonify(government.get_user_requests())


@app.route('/getTransferRequests', methods=['POST', 'GET'])
def get_transfer_requests():
    return jsonify(government.get_transfer_requests())


@app.route('/getUserDetails', methods=['POST'])
def get_user_details():
    req = rapidjson.loads(request.data)
    public_key = req['public_key']
    return jsonify(database_helper.get_user_details(public_key))


@app.route('/getSurveyorDetails', methods=['POST'])
def get_surveyor_details():
    if user.get_user_type() != "SURVEYOR":
        return {"success": False, "message": "User is not SURVEYOR"}
    return jsonify(database_helper.get_surveyor_details(user.get_system_user()['pub.key']))


@app.route('/transferLand', methods=['POST'])
def transfer_land():
    req = rapidjson.loads(request.data)
    survey_number = req['surveyNumber']
    divisions = req['divisions']
    transaction_id = req['transaction_id']
    to_public_key = req['public_key']
    output_index = req['output_index']
    return jsonify(
        land_transactions.transfer_land(survey_number, transaction_id, output_index, to_public_key, divisions))


@app.route('/getUserAssets', methods=['GET', 'POST'])
def get_user_assets():
    return jsonify({"success": True, "data": land_transactions.get_user_assets()})


@app.route('/')
def login_page():
    return render_template('index.html')


@app.errorhandler(404)
@app.errorhandler(401)
def serve_error(error):
    if "401" in str(error):
        code = 401
        message = "You are not supposed to do this thing!"
    else:
        code = 404
        message = "You don't have good Typing Skills!"
    return render_template('page_not_found.html', code=code, message=message), code


if __name__ == '__main__':
    app.run(port=8080, host="0.0.0.0", debug=True)
