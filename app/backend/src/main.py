from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

PUBLIC_FOLDER = '/app/frontend/public'
SRC_FOLDER = '/app/frontend/src'

@app.route('/')
def index():
    """ 
    Index route 
    """
    return send_from_directory(PUBLIC_FOLDER, 'index.html')

@app.route('/map')
def map_view():
    """ 
    Test for frontend display map 
    """
    return send_from_directory(PUBLIC_FOLDER, 'map.html')

@app.route('/<path:filename>')
def public_files(filename):
    """
    Public html files
    """
    return send_from_directory(PUBLIC_FOLDER, filename)

@app.route('/src/<path:filename>')
def src_files(filename):
    """ 
    js content and animations
    """
    return send_from_directory(SRC_FOLDER, filename)

@app.route("/assets/<path:filename>")
def assets_files(filename):
    """ 
    Assets content and animations
    """
    models_dir = os.path.join(os.getcwd(), "frontend", "assets")
    file_path = os.path.join(models_dir, filename)
    directory = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)
    return send_from_directory(directory, file_name)

@app.route('/api/rewind', methods=['POST'])
def rewind():
    """
    Notification after index login
    """
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
