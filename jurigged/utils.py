import fnmatch
import os
import types

from ovld import ovld

##########
# Locate #
##########


@ovld
def locate(fn: types.FunctionType, catalog):
    return locate(fn.__code__, catalog)


@ovld
def locate(code: types.CodeType, catalog):
    key = ("FunctionCode", code.co_filename, code.co_firstlineno)
    return catalog.get(key, None)


@ovld
def locate(typ: type, catalog):
    key = f"{typ.__module__}.{typ.__qualname__}"
    return catalog.get(key, None)


@ovld
def locate(mod: types.ModuleType, catalog):
    return catalog.get(mod.__name__, None)


@ovld
def locate(obj: object, catalog):  # pragma: no cover
    return None


###########
# Conform #
###########


class ConformException(Exception):
    pass


@ovld.dispatch
def conform(self, obj1, obj2):
    if hasattr(obj1, "__conform__"):
        obj1.__conform__(obj2)
    else:
        self.resolve(obj1, obj2)(obj1, obj2)


@ovld
def conform(self, obj1: types.FunctionType, obj2: types.FunctionType):
    fv1 = obj1.__code__.co_freevars
    fv2 = obj2.__code__.co_freevars
    if fv1 != fv2:
        msg = (
            f"Cannot replace closure `{obj1.__name__}` because the free "
            f"variables changed. Before: {fv1}; after: {fv2}."
        )
        if ("__class__" in (fv1 or ())) ^ ("__class__" in (fv2 or ())):
            msg += " Note: The use of `super` entails the `__class__` free variable."
        raise ConformException(msg)
    obj1.__code__ = obj2.__code__
    obj1.__defaults__ = obj2.__defaults__
    obj1.__kwdefaults__ = obj2.__kwdefaults__


@ovld
def conform(self, obj1, obj2):
    pass


########
# Misc #
########


class EventSource(list):
    def __init__(self, *, save_history=False):
        if save_history:
            self._history = []
        else:
            self._history = None

    def register(self, listener, apply_history=True):
        if self._history and apply_history:
            for args, kwargs in self._history:
                listener(*args, **kwargs)
        self.append(listener)
        return listener

    def emit(self, *args, **kwargs):
        for listener in self:
            listener(*args, **kwargs)
        if self._history is not None:
            self._history.append((args, kwargs))


def glob_filter(pattern):
    if pattern.startswith("~"):
        pattern = os.path.expanduser(pattern)
    elif not pattern.startswith("/"):
        pattern = os.path.abspath(pattern)

    if os.path.isdir(pattern):
        pattern = os.path.join(pattern, "*")

    def matcher(filename):
        return fnmatch.fnmatch(filename, pattern)

    return matcher
