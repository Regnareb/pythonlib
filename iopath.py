import os
import re
import sys
import json
import errno
import pickle
import logging
import subprocess
from contextlib import contextmanager
from . import utils
from . import common
logger = logging.getLogger(__name__)


def formatpath(filename, path='', prefix='', suffix=''):
    """Create a complete path with a filename, a path and prefixes/suffixes
    /path/prefix_filename_suffix.ext"""
    path = os.path.join(path, "")  # Delete ?
    if suffix:
        suffix = '_' + suffix
    if prefix:
        prefix = prefix + '_'
    filename, fileExt = os.path.splitext(filename)
    filePath = os.path.join(path, prefix + filename + suffix + fileExt)
    return filePath


def normpath(path):
    """Fix some problems with some programs not accepting backward slashes in file paths"""
    return os.path.normpath(path).replace('\\', '/')


def pathjoin(*args):
    path = os.path.join(*args)
    return normpath(path)


def get_envvars_from_string(string):
    regex = r'(?<=\$)[A-Z]*'  # Take digits into account?
    envvars = re.findall(regex, string)
    return envvars


def get_envvar_path(path, envvar):
    """Return the path converted to a path with the environment variable replacing a part of the path if it's possible."""
    path = normpath(path)
    envpath = normpath(os.getenv(envvar))
    path = path.replace(envpath, f'${envvar}')
    return path


def get_relative_path(path, envvar):
    """Convert path to a relative path from path in environment variable
    /foo/bar/ and /foo/bar2/ will return ../bar/
    The environment variable path can only be a directory, not a file
    On Windows, it will raise a ValueError if the two paths are not on the same disk
    """
    path = normpath(path)
    envpath = normpath(os.getenv(envvar))
    return os.path.relpath(path, envpath)


def get_absolute_path(path, envvars=[]):
    """Convert a path with an environment variable inside it, to a full absolute path if the env var exists"""
    if not envvars:
        envvars = get_envvars_from_string(path)
    for var in envvars:
        path = path.replace(f'${var}', os.getenv(var))
    return path


def create_dir(path):
    """Creates a directory"""
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def pickle_object(fullPath, toPickle):
    """Pickle an object at the designated path"""
    with open(fullPath, 'w') as f:
        pickle.dump(toPickle, f)
    f.close()


def unpickle_object(fullPath):
    """unPickle an object from the designated file path"""
    with open(fullPath, 'r') as f:
        frompickle = pickle.load(f)
    f.close()
    return frompickle


def json_write(data, filepath, default=None):
    with open(filepath, 'w') as outfile:
        json.dump(data, outfile, default=default)


def json_load(filepath):
    with open(filepath, 'r') as dataFile:
        return json.load(dataFile)


def get_file_sequence(filepath, prefix='', pattern=None, suffix='', padding=None):
    """Detect if the filepath is a single file or a sequence.
    If it's a sequence, replace the frame number with prefix + pattern + suffix.
    Example: <%3> or $F3
    Returns (is_sequence, filepath).
    """
    folder, filename = os.path.split(filepath)
    regex = r'\d+' if padding is None else rf'(?<!\d)\d{{{padding}}}(?!\d)'

    # Prefer the last number in the name (typically the frame number)
    for match in reversed(list(re.finditer(regex, filename))):
        num_len = len(match.group())
        head, tail = filename[:match.start()], filename[match.end():]

        frames = find_frames(folder, head, tail, num_len)
        if len(frames) > 1:
            pat = str(num_len) if pattern is None else pattern
            seq_name = f"{head}{prefix}{pat}{suffix}{tail}"
            return True, pathjoin(folder, seq_name), frames
    return False, filepath, []


def find_frames(folder, head, tail, num_len):
    """Return the frame numbers of all files matching head + num_len + tail."""
    frame_re = re.compile(rf'{re.escape(head)}(\d{{{num_len}}}){re.escape(tail)}')
    frames = []
    for name in os.listdir(folder):
        m = frame_re.fullmatch(name)
        if m:
            frames.append(m.group(1))
    return sorted(frames, key=int)


def openfolder(path):
    """For each OS platform open the explorer on the path passed as argument"""
    if sys.platform.startswith('linux'):
        return subprocess.Popen(['xdg-open', '--', path])
    elif sys.platform in ['win32', 'cygwin']:
        path = path.replace('/', '\\')
        return subprocess.Popen(['explorer', path])
    elif sys.platform == 'darwin':
        return subprocess.Popen(['open', '--', path])


def openfile(path):
    """For each OS platform execute the file path passed as argument"""
    if sys.platform.startswith('linux'):
        subprocess.call(('xdg-open', path))
    elif sys.platform in ['win32', 'cygwin']:
        os.startfile(path)
    elif sys.platform == 'darwin':
        subprocess.call(('open', path))



@contextmanager
def pause_services(services, strict=False):
    if not utils.is_admin():
        services = []
        logger.error("No administrator rights, can't pause Windows Services")
        if strict:
            raise RuntimeError

    for service in services:
        subprocess.Popen(f'net stop "{service}"', creationflags=subprocess.CREATE_NO_WINDOW)
    yield
    for service in services:
        subprocess.Popen(f'net start "{service}"', creationflags=subprocess.CREATE_NO_WINDOW)


@contextmanager
def pause_processes(processes, pssuspend_path='pssuspend.exe'):
    if sys.platform in ['win32', 'cygwin']:
        for process in processes:
            subprocess.Popen(f'{pssuspend_path} "{process}"', creationflags=subprocess.CREATE_NO_WINDOW, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        yield
        for process in processes:
            subprocess.Popen(f'{pssuspend_path} -r "{process}"', creationflags=subprocess.CREATE_NO_WINDOW, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    else:
        for process in processes:
           subprocess.Popen(f'pkill -TSTP "{process}$"', shell=True)
        yield
        for process in processes:
            subprocess.Popen(f'pkill -CONT "{process}$"', shell=True)


def download_pssuspend(path):
    """pssuspend is a Windows software that can pause and resume executable on the fly"""
    import requests
    from io import BytesIO
    from zipfile import ZipFile
    url = 'https://download.sysinternals.com/files/PSTools.zip'
    response = requests.get(url)
    zipfile = ZipFile(BytesIO(response.content))
    pssuspend = zipfile.extract('pssuspend.exe', path)
    pssuspend = zipfile.extract('pssuspend64.exe', path)
    return pssuspend
