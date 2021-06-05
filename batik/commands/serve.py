from io import BytesIO
import os 
from flask import Flask, request, jsonify, make_response, abort, send_file
from flask_socketio import SocketIO
import socketio

app = Flask(__name__)
from flask_cors import CORS

import sys

#import ray

from batik import manifest

#ray.init()
state = manifest.parse_from_file()

from .base import Base


@app.route('/reload_manifest', methods=['POST'])
def reload_manifest():
    global state
    state = manifest.parse_from_file()
    return "ok", 200


@app.route('/manifest', methods=['GET'])
def get_manifest():
    return jsonify(state), 200


@app.route('/endpoint/<ep>', methods=['POST'])
def run_exp(ep):

    #res = manifest.endpoint_run(state, ep, request.args)
    res = manifest.endpoint_run(state, ep, request.data)

    # HACK
    if type(res) is BytesIO:
        return send_file(res,mimetype='image/png', attachment_filename='plot.png')
    else:
        return jsonify(res), 200


class Serve(Base):
    """Serve models"""

    def run(self):
        app.run(host='0.0.0.0', port=5678)