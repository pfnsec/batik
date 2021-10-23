from io import BytesIO
import os.path
from flask import Flask, request, jsonify, make_response, abort, send_file
from flask_socketio import SocketIO

from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from watchdog.observers import Observer


app = Flask(__name__)

import sys

from batik import manifest


from .base import Base

manifest_instance = None

@app.route('/reload_manifest', methods=['POST'])
def reload_manifest():
    global manifest_instance
    manifest_instance = manifest.parse_from_file()
    return "ok", 200


@app.route('/manifest', methods=['GET'])
def get_manifest():
    return jsonify(manifest_instance), 200


@app.route('/endpoint/<ep>', methods=['POST'])
def run_exp(ep):

    payload = request.json
    payload = manifest_instance.cast_endpoint_payload(ep, payload)

    res = manifest_instance.run_endpoint(ep, payload)

    # HACK
    if type(res) is BytesIO:
        return send_file(res,mimetype='image/png', attachment_filename='plot.png')
    else:
        return jsonify(res), 200


class Serve(Base):
    """Serve models"""
    def __init__(self, options, *args, **kwargs):
        global manifest_instance
        super().__init__(options, args, kwargs)
        manifest_instance = manifest.parse_from_file()


    def run(self):


        if(self.options['--hot-reload']):
            print("Starting hot-reload...")
            self.start_reload()

        manifest_instance.spawn_daemons()

        #socketio = SocketIO(app)

        app.run(host='0.0.0.0', port=5678)
        #socketio.run(app, host='0.0.0.0', port=5678)
    

    def start_reload(self):
        global state

        observer = Observer()

        class EventHandler(FileSystemEventHandler):
            def on_modified(self, event: FileModifiedEvent):
                if event.src_path.startswith('./__pycache__'):
                    return

                f, e = os.path.splitext(event.src_path)
                if e not in [".py", ".yaml"]:
                    return

                print("Reloading...")
                global manifest_instance
                manifest_instance = manifest.parse_from_file()

        observer.schedule(EventHandler(), "./", recursive=True)
        observer.start()