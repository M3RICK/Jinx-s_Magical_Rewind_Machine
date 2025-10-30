from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

FRONTEND_FOLDER = '/app/frontend/src'
PUBLIC_FOLDER = '/app/frontend/public'

@app.route('/')
def index():
    return send_from_directory(FRONTEND_FOLDER, 'index.html')

@app.route('/public/<path:filename>')
def static_files(filename):
    return send_from_directory(PUBLIC_FOLDER, filename)

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
