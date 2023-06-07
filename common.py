import re
import os
import time
import math
import inspect
import logging
import itertools
import functools
from collections import Iterable
logger = logging.getLogger(__name__)


def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = itertools.tee(iterable)
    next(b, None)
    return itertools.izip(a, b)


def set_tolist_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError


def get_firstitem(iterable, default=None):
    """Return the first item if any"""
    if iterable:
        for item in iterable:
            return item
    return default


def flatten(coll):
    """Flatten a list while keeping strings"""
    for i in coll:
        if isinstance(i, Iterable) and not isinstance(i, basestring):
            for subc in flatten(i):
                yield subc
        else:
            yield i


def natural_sort_key(iterable):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(iterable, key=alphanum_key)


def natural_sort_key2(s, _nsre=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower() for text in _nsre.split(s)]


def string2bool(string, strict=True):
    """Convert a string to its boolean value.
    The strict argument keep the string if neither True/False are found
    """
    if not isinstance(string, basestring):
        return string
    if strict:
        return string.capitalize() == 'True'
    else:
        if string.capitalize() == 'True':
            return False
        elif string.capitalize() == 'False':
            return True
        else:
            return string


def camelcase_separator(label, separator=' '):
    """Convert a CamelCase to words separated by separator"""
    return re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r'%s\1' % separator, label)


def tonumber(s):
    """Convert a string to an int or a float depending of their types"""
    try:
        return int(s)
    except ValueError:
        return float(s)


def rgb2hex(rgb):
    """Convert a rgb color (0, 0, 0) to hexadecimal one (#000000)
    It takes as argument either a string with different float numbers
    or directly a list or tuple of strings, ints or floats (normalised rgb)
    """
    if isinstance(rgb, basestring):
        rgb = re.findall(r'([\d|\.]+)', rgb)
        rgb = [tonumber(i) for i in rgb]
    if isinstance(rgb, Iterable):
        if isinstance(rgb[0], basestring):
            rgb = [tonumber(i) for i in rgb]
        if isinstance(rgb[0], float):
            rgb = [int(i*255) for i in rgb]  # Convert 0-1 based rgb to 255 values
    rgb = [max(0, min(i, 255)) for i in rgb]  # Clamp rgb values
    return "#{0:02x}{1:02x}{2:02x}".format(*rgb)


def hex2rgb(hexcode):
    return tuple(map(ord, hexcode[1:].decode('hex')))


def shorten_string(string, maxlimit, separator='.. '):
    if len(string) <= maxlimit:
        return string
    elif len(string) <= len(separator) + 2:
        return string[:maxlimit - 2] + '..'
    else:
        beginning = int(math.ceil(maxlimit / 2.))
        end = (maxlimit - beginning) * - 1
        return (string[:beginning] + separator + string[end:]) if len(string) > maxlimit else string


def increment_string(s):
    return re.sub('(\d*)$', lambda x: str(int(x.group(0)) + 1), s)


def replace_extension(path, ext):
    if ext and not ext.startswith('.'):
        ext = ''.join(['.', ext])
    return path.replace(os.path.splitext(path)[1], ext)


def humansize(nbytes):
    suffixes = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']
    if nbytes == 0:
        return '0 B'
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])


def lstrip_all(toStrip, stripper):
    if toStrip.startswith(stripper):
        return toStrip[len(stripper):]
    return toStrip


def rstrip_all(toStrip, stripper):
    if toStrip.endswith(stripper):
        return toStrip[:-len(stripper)]
    return toStrip





class Enum():
    """An infinite loop between all elements of a list,
    Usefull for having an incremental "toggle"
    """
    def __init__(self, enum_list):
        self.enum_list = itertools.cycle(enum_list)

    def next(self, current=None):
        if current not in self.enum_list:
            return next(self.enum_list)
        for i in self.enum_list:
            if i==current:
                return next(self.enum_list)







def withmany(method):
    """A decorator that iterate through all the elements and eval each one if a list is in input"""
    @functools.wraps(method)
    def many(many_foos):
        for foo in many_foos:
            yield method(foo)
    method.many = many
    return method


def memoize_single(f):
    """Memoization decorator for a function taking a single argument"""
    class memodict(dict):
        def __missing__(self, key):
            ret = self[key] = f(key)
            return ret
    return memodict().__getitem__


def memoize_several(f):
    """Memoization decorator for functions taking one or more arguments"""
    class memodict(dict):
        def __init__(self, f):
            self.f = f

        def __call__(self, *args):
            return self[args]

        def __missing__(self, key):
            ret = self[key] = self.f(*key)
            return ret
    return memodict(f)


def elapsed_time(f):
    @functools.wraps(f)
    def elapsed(*args, **kwargs):
        start = time.time()
        result = f(*args, **kwargs)
        elapsed = time.time() - start
        logger.debug(elapsed)
        return result
    return elapsed


def restore_environment(f):
    @functools.wraps(f)
    def func(*args, **kwargs):
        old = os.environ.copy()
        result = f(*args, **kwargs)
        os.environ.update(old)
        return result
    return func


def decorate_all(decorator):
    # Decorate all methods of the class with the decorator passed as argument (Python 3)
    def decorate(cls):
        for name, fn in inspect.getmembers(cls, inspect.isroutine):
            if name != '__new__':
                setattr(cls, name, decorator(fn))
        return cls
    return decorate
