import os
import re
import logging


_verbosity_levels = {
    1: logging.DEBUG,
    2: logging.INFO,
    3: logging.WARN,
    4: logging.ERROR
}
LOG_FORMAT = "%(asctime)-15s %(process)d %(message)s"
LOG_LEVEL = _verbosity_levels[int(os.environ.get('VERBOSITY', 1))]
MAX_HEADER_LENGTH = int(os.environ.get('MAX_HEADER_LENGTH', 4096))
MAX_BODY_LENGTH = 2 ** (32) - 400000 # This should be safer, TODO later
LOGFILE = os.environ.get('LOGFILE', './logs/logs')
NUMBER_OF_FILESERVERS = int(os.environ['NUMBER_OF_FILESERVERS'])
NUMBER_OF_RESPONDERS = int(os.environ.get('NUMBER_OF_RESPONDERS', 10))
NUMBER_OF_PROCESSERS = int(os.environ.get('NUMBER_OF_PROCESSERS', 10))
REQUESTS_PORT = int(os.environ.get('REQUESTS_PORT', 8080))
RESPONSES_PORT = int(os.environ.get('RESPONSES_PORT', 8090))
FILESERVERS_PORTS = int(os.environ.get('FILESERVERS_PORTS', 8070))
REQUESTS_SOCKET_LENGTH = int(os.environ.get('REQUESTS_SOCKET_LENGTH', 10))
RESPONSES_SOCKET_LENGTH = int(os.environ.get('RESPONSES_SOCKET_LENGTH', 10))
FILESERVER_NAME = os.environ.get('FILESERVER_NAME', None)
FILESERVER_PREFIX = os.environ.get('FILESERVER_PREFIX', 'tp1_file_')
VALID_POST_URI_REGEX = re.compile('^/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$')
VALID_PUT_GET_DELETE_URI_REGEX = re.compile('^/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$')
STATUS_CODE_MESSAGES = {
    200: "OK",
    201: "OK",
    400: "Bad Request",
    500: "Internal Error",
    404: "Not Found"
}
