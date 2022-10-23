import json
from typing import Dict

class Message:
    def __init__(self):
        pass

class InvokeRequest(Message):
    def __init__(self, endpoint, payload, tag=None, trace=False):
        self.endpoint = endpoint
        self.payload = payload
        self.tag = tag
        self.trace = trace

    def to_dict(self):
        return {
            'cmd': 'invoke_request',
            'endpoint': self.endpoint,
            'payload': self.payload,
            'tag': self.tag,
            'trace': self.trace,
        }

class InvokeAck(Message):
    def __init__(self, tag, errors=[]):
        self.errors = errors 
        self.tag = tag

    def to_dict(self):
        return {
            'cmd': 'invoke_ack',
            'error': self.errors,
            'tag': self.tag,
        }

class InvokeTrace(Message):
    def __init__(self, node, timestamp, payload, tag):
        self.node = node
        self.timestamp = timestamp
        self.payload = payload
        self.tag = tag

    def to_dict(self):
        return {
            'cmd': 'invoke_trace',
            'timestamp': self.timestamp,
            'node': self.node,
            'payload': self.payload,
            'tag': self.tag,
        }

class InvokeResponse(Message):
    def __init__(self, payload, tag):
        self.payload = payload
        self.tag = tag

    def to_dict(self):
        return {
            'cmd': 'invoke_response',
            'payload': self.payload,
            'tag': self.tag,
        }


def message_from_dict(msg: Dict):
    cmd = msg['cmd']
    if cmd == 'invoke_request':
        return InvokeRequest(
            msg['endpoint'],
            msg['payload'],
            msg['tag'],
            msg['trace'],
        )
    elif cmd == 'invoke_response':
        return InvokeResponse(
            msg['payload'],
            msg['tag'],
        )