import logging

class Layer:
    def __init__(self, layer_args={}, **kwargs): 
        self.layer_args = layer_args
    def _run(self, payload):
        # TODO: Log data output here
        res = self.run(payload)
        return res
        



class Actor:
    def __init__(self, actor_args={}, **kwargs): 
        self.actor_args = actor_args
    def _run(self, payload):
        try: 
            return self.run(payload)
        except Exception as e:
            logging.exception('')
