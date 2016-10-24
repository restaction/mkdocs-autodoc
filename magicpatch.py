"""
Patch functions in magic way

Usage:

    >>> from magicpatch import patch
    >>> def func(x):
    ...     return x
    ...
    >>> @patch(func)
    ... def patch_func(be_patched, x):
    ...     return 2*be_patched(x)
    ...
    >>> func(1)
    2
    >>>
"""
import uuid
import types
import functools


def copy_func(f):
    """
    Deep copy function of Python3.

    Based on:
    http://stackoverflow.com/a/6528148/190597 (Glenn Maynard)
    http://stackoverflow.com/questions/13503079/how-to-create-a-copy-of-a-python-function (Aaron Hall)
    """  # noqa
    g = types.FunctionType(
        f.__code__, f.__globals__, f.__name__,
        f.__defaults__, f.__closure__
    )
    g = functools.update_wrapper(g, f)
    g.__kwdefaults__ = f.__kwdefaults__
    return g


PATCHED = {}


def patch(f_be_patched):
    def decorater(f):
        key = str(uuid.uuid4())
        PATCHED[key] = functools.partial(f, copy_func(f_be_patched))
        code = """
def wrapper(*args, **kwargs):
    return __import__("magicpatch").PATCHED["{}"](*args, **kwargs)
        """.format(key)
        context = {}
        exec(code, context)
        f_be_patched.__code__ = context["wrapper"].__code__
        return f
    return decorater
