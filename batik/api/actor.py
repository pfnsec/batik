from batik.api.util import actor_by_path

class Actor:
    # Actor's kwargs are contained within the underlying actor class
    def __init__(self, class_path, kwargs):
        if kwargs is None:
            self.cl = actor_by_path(class_path)()
        else:
            self.cl = actor_by_path(class_path)(**kwargs)