import os
import urllib
import logging
logger = logging.getLogger(__name__)


def download_file(url, save_path):
    try:
        response = urllib.request.urlopen(url)
        with open(save_path, 'wb') as f:
            f.write(response.read())
        return True
    except urllib.error.HTTPError as e:
        logger.error(f"Error code from server: {e.code} \n {e.read().decode()}")
    except urllib.error.URLError as e:
        logger.error(f"Impossible to joinde: {e.reason}")
    return False


def get_filename_from_url(url):
    parsed = urllib.parse.urlparse(url)
    filename = os.path.basename(parsed.path)
    return filename
