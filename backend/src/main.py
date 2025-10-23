from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_FOLDER = os.path.join(PROJECT_ROOT, 'frontend')
STATIC_FOLDER = os.path.join(FRONTEND_FOLDER, 'static')

@app.route('/')
def index():
    return send_from_directory(FRONTEND_FOLDER, 'index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(STATIC_FOLDER, filename)

@app.route('/api/rewind', methods=['POST'])
def rewind():
    data = request.get_json()
    username = data.get('username')
    hashtag = data.get('hashtag')
    server = data.get('server')

    return jsonify({
        "message": f"Summoner {username}{hashtag} from {server} received!",
        "username": username,
        "hashtag": hashtag,
        "server": server
    })

if __name__ == '__main__':
    app.run()
