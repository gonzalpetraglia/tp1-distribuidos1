import os
import re
LOGFILE = os.environ.get('LOGFILE', './logs/logs')
NUMBER_OF_FILESERVERS = int(os.environ['NUMBER_OF_FILESERVERS'])
NUMBER_OF_RESPONDERS = int(os.environ.get('NUMBER_OF_RESPONDERS', 10))
NUMBER_OF_PROCESSERS = int(os.environ.get('NUMBER_OF_PROCESSERS', 10))
REQUESTS_PORT = int(os.environ.get('REQUESTS_PORT', 8080))
RESPONSES_PORT = int(os.environ.get('RESPONSES_PORT', 8090))
FILESERVERS_PORTS = int(os.environ.get('FILESERVERS_PORTS', 8070))
FILESERVER_NAME = os.environ.get('FILESERVER_NAME', None)
FILESERVER_PREFIX = os.environ.get('FILESERVER_PREFIX', 'tp1_file_')
VALID_POST_URI_REGEX = re.compile('^/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$')
VALID_PUT_GET_DELETE_URI_REGEX = re.compile('^/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$')
STATUS_CODE_MESSAGES = {
    200: "OK",
    400: "Bad Request",
    500: "Internal Error",
    404: "Not Found"
}
