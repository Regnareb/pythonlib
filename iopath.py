import os
import sys
import json
import errno
import pickle
import ctypes
import socket
import smtplib
import logging
import subprocess
from io import BytesIO
from zipfile import ZipFile
from contextlib import contextmanager
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
logger = logging.getLogger(__name__)


def formatpath(fileName, path='', prefix='', suffix=''):
    """ Create a complete path with a filename, a path and prefixes/suffixes
    /path/prefix_filename_suffix.ext"""
    path = os.path.join(path, "")  # Delete ?
    if suffix:
        suffix = '_' + suffix
    if prefix:
        prefix = prefix + '_'
    fileName, fileExt = os.path.splitext(fileName)
    filePath = os.path.join(path, prefix + fileName + suffix + fileExt)
    return filePath


def normpath(path):
    """Fix some problems with Maya evals or some file commands needing double escaped anti-slash '\\\\' in the path in Windows"""
    return os.path.normpath(path).replace('\\', '/')


def pathjoin(*args):
    path = os.path.join(*args)
    return normpath(path)


def create_dir(path):
    """Creates a directory"""
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def pickle_object(fullPath, toPickle):
    """ Pickle an object at the designated path """
    with open(fullPath, 'w') as f:
        pickle.dump(toPickle, f)
    f.close()


def unpickle_object(fullPath):
    """ unPickle an object from the designated file path """
    with open(fullPath, 'r') as f:
        fromPickle = pickle.load(f)
    f.close()
    return fromPickle


def json_write(data, filePath, default=None):
    with open(filePath, 'w') as outfile:
        json.dump(data, outfile, default=default)


def json_load(filePath):
    with open(filePath, 'r') as dataFile:
        return json.load(dataFile)


def openfolder(path):
    if sys.platform.startswith('darwin'):
        return subprocess.Popen(['open', '--', path])
    elif sys.platform.startswith('linux'):
        return subprocess.Popen(['xdg-open', '--', path])
    elif sys.platform.startswith('win32'):
        path = path.replace('/', '\\')
        return subprocess.Popen(['explorer', path])


def openfile(path):
    if sys.platform.startswith('darwin'):
        subprocess.call(('open', path))
    elif os.name == 'nt':
        os.startfile(path)
    elif os.name == 'posix':
        subprocess.call(('xdg-open', path))


def internet(host="8.8.8.8", port=53, timeout=3):
  """
  Host: 8.8.8.8 (google-public-dns-a.google.com)
  OpenPort: 53/tcp
  Service: domain (DNS/TCP)
  """
  try:
    socket.setdefaulttimeout(timeout)
    socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
    return True
  except socket.error as ex:
    logger.exception(ex)
    return False


def send_mail(sender, receivers, subject, text='', html=''):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(receivers)
    text = MIMEText(text, 'plain')
    html = MIMEText(html, 'html')
    msg.attach(text)
    msg.attach(html)
    try:
        s = smtplib.SMTP('localhost')
        s.sendmail(sender, receivers, msg.as_string())
        s.quit()
        return True
    except smtplib.SMTPException:
        logger.error('Error: unable to send email')
        return False


@contextmanager
def pause_services(services):
    if sys.platform=='win32':
        admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        if admin:
            for service in services:
                subprocess.Popen('net stop "{}"'.format(service), creationflags=subprocess.CREATE_NO_WINDOW)
        elif services:
            logger.warning("No administrator rights, can't pause Windows Services")
        yield
        if admin:
            for service in services:
                subprocess.Popen('net start "{}"'.format(service), creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        yield


@contextmanager
def pause_processes(processes):
    if sys.platform in ['Windows', 'win32', 'cygwin']:
        for process in processes:
            subprocess.Popen('lib/pssuspend.exe "{}"'.format(process), creationflags=subprocess.CREATE_NO_WINDOW, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        yield
        for process in processes:
            subprocess.Popen('lib/pssuspend.exe -r "{}"'.format(process), creationflags=subprocess.CREATE_NO_WINDOW, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    else:
        for process in processes:
           subprocess.Popen('pkill -TSTP "{}$"'.format(process), shell=True)
        yield
        for process in processes:
            subprocess.Popen('pkill -CONT "{}$"'.format(process), shell=True)


def download_pssuspend(path):
    import requests
    url = 'https://download.sysinternals.com/files/PSTools.zip'
    response = requests.get(url)
    zipfile = ZipFile(BytesIO(response.content))
    pssuspend = zipfile.extract('pssuspend.exe', path)
    pssuspend = zipfile.extract('pssuspend64.exe', path)
    return pssuspend
