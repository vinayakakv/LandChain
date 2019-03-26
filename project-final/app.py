import json

from flask import Flask, render_template, send_from_directory, request, jsonify

from cryptoland.land_operations import Survey
from cryptoland.user_config import UserConfig

app = Flask(__name__, static_url_path='')
user = UserConfig()


@app.route('/<path:outerdir>/<path:path>')
def send_file(outerdir, path):
    return send_from_directory('templates/', outerdir + '/' + path + '.html')


@app.route('/saveSurvey', methods=['POST'])
def save_survey():
    if user.get_user_type() != "SURVEYOR":
        return jsonify({"success": False, "message": "Only Surveyor can survey"})
    s = Survey(request.data)
    return jsonify({"success": True, "data": json.loads(str(s))})


@app.route('/getSurveys', methods=['POST', 'GET'])
def get_surveys():
    return jsonify({"success": True, "data": Survey.get_surveys()})


@app.route('/getSystemUser', methods=['POST', 'GET'])
def get_system_user():
    return jsonify({"success": True, "data": user.get_system_user()})


@app.route('/addSystemUser', methods=['POST', 'GET'])
def add_system_user():
    req = json.loads(request.data)
    user_name = req['user_name']
    return jsonify(user.create_user(user_name))


@app.route('/registerUser', methods=['POST'])
def register_user():
    req = json.loads(request.data)
    public_key = req['public_key']
    user_type = req['user_type'].strip().upper()
    return jsonify(user.register_user(public_key, user_type))


@app.route('/getRegisteredUsers', methods=['POST', 'GET'])
def get_registered_users():
    return jsonify(user.get_registered_users())


@app.route('/getUserRequests', methods=['POST', 'GET'])
def get_user_requests():
    return jsonify(user.get_user_requests())


@app.route('/')
def login_page():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(port=8080, host="0.0.0.0", debug=True)
