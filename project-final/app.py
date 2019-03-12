from flask import Flask, render_template, send_from_directory, request, jsonify
from cryptoland.land_operations import Survey

app = Flask(__name__, static_url_path='')


@app.route('/surveyor/<path:path>')
def send_file(path):
    return send_from_directory('templates/surveyor', path + '.html')


@app.route('/saveSurvey', methods=['POST'])
def save_survey():
    print(request.data)
    s = Survey(request.data)
    return jsonify({"success": True, "data": s.__dict__})


@app.route('/getSurveys', methods=['POST', 'GET'])
def get_surveys():
    return jsonify(Survey.get_surveys())


@app.route('/')
def login_page():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(port=8080, host="0.0.0.0", debug=True)
