import os
import logging
_verbosity_levels = {
    1: logging.DEBUG,
    2: logging.INFO,
    3: logging.WARN,
    4: logging.ERROR
}
LOG_FORMAT = "%(asctime)-15s %(process)d %(message)s"
LOG_LEVEL = _verbosity_levels[int(os.environ.get('VERBOSITY', 1))]
FILES_FOLDER = os.environ.get('FILES_FOLDER', './files')
RESPONSES_PORT = int(os.environ.get('RESPONSES_PORT', 8090))
FILESERVERS_PORTS = int(os.environ.get('FILESERVERS_PORTS', 8070))
MAINSERVER_NAME = os.environ.get('MAINSERVER_NAME', 'tp1_main_1')
FILESERVER_WORKERS = int(os.environ.get('FILESERVER_WORKERS', 10))
CACHE_CAPACITY = int(os.environ.get('CACHE_CAPACITY', 10))
FILESERVER_HOST_BIND = os.environ.get('FILESERVER_HOST_BIND', '0.0.0.0')
