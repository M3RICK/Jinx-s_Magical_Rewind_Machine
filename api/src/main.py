from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello World'

if __name__ == '__main__':
    app.run()
