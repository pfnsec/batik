from io import BytesIO
import os 
from flask import Flask, request, jsonify, make_response, abort, send_file

app = Flask(__name__)

import sys

from batik import manifest

state = {}

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

    print(request.data)

    res = manifest.endpoint_run(state, ep, request.data)

    # HACK
    if type(res) is BytesIO:
        return send_file(res,mimetype='image/png', attachment_filename='plot.png')
    else:
        return jsonify(res), 200


class Serve(Base):
    """Serve models"""
    def __init__(self, options, *args, **kwargs):
        super().__init__(options, args, kwargs)
        global state
        state = manifest.parse_from_file()


    def run(self):
        app.run(host='0.0.0.0', port=5678)