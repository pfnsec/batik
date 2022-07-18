import sys
import importlib
import inspect

def actor_by_path(name):
    module_name, class_name = name.split(".")

    if './' not in sys.path:
        sys.path.append('./')

    if module_name in sys.modules:
        somemodule = importlib.reload(sys.modules[module_name])
    else:
        somemodule = importlib.import_module(module_name)

    cl = getattr(somemodule, class_name)

    return cl


def func_by_path(name, *args, **kwargs):
    ns = name.split(".")

    module_name = '.'.join(ns[0:-1])
    func_name   = ns[-1]

    if './' not in sys.path:
        sys.path.append('./')

    if module_name in sys.modules:
        somemodule = importlib.reload(sys.modules[module_name])
    else:
        somemodule = importlib.import_module(module_name)

    fn = getattr(somemodule, func_name)

    return fn


async def run_or_await(fn, *args, **kwargs):
    if inspect.iscoroutinefunction(fn):
        return await fn(*args, **kwargs)
    else:
        return fn(*args, **kwargs)
