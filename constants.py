import re

REGEX_WINDOWS_PATH = re.compile(r'^[a-zA-Z]:(?:\\|/)(?:[^\\/:*?"<>|\r\n]+(?:\\|/))*[^\\/:*?"<>|\r\n]*$', flags=re.MULTILINE)
REGEX_UNIX_PATH = re.compile(r'^(\/[^\/ ]*)+\/?$', flags=re.MULTILINE)    # Do not take into account filenames with spaces in it
REGEX_URL = re.compile(r'^https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+,.~#?&\/=]*)$', flags=re.MULTILINE)
