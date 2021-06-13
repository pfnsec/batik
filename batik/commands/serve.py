from io import BytesIO
import os 
from flask import Flask, request, jsonify, make_response, abort, send_file

from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from watchdog.observers import Observer


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


    res = manifest.endpoint_run(state, ep, request.json)

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
        global state
        if(self.options['--hot-reload']):
            print("Starting hot-reload...")
            self.start_reload()
        app.run(host='0.0.0.0', port=5678)
    

    def start_reload(self):
        global state

        observer = Observer()

        class EventHandler(FileSystemEventHandler):
            def on_modified(self, event: FileModifiedEvent):
                if event.src_path.startswith('./__pycache__'):
                    return

                print("Reloading...")
                global state
                state = manifest.parse_from_file()


                #if event.is_directory:
                #    return
                #if event.src_path == fileabspath:
                #    this._reload()

        observer.schedule(EventHandler(), "./", recursive=True)
        observer.start()