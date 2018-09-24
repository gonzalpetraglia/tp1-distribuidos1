import os
FILES_FOLDER = os.environ.get('FILES_FORDER', './files')
RESPONSES_PORT = int(os.environ.get('RESPONSES_PORT', 8090))
FILESERVERS_PORTS = int(os.environ.get('FILESERVERS_PORTS', 8070))
MAINSERVER_NAME = os.environ.get('MAINSERVER_NAME', 'tp1_main_1')
FILESERVER_WORKERS = int(os.environ.get('FILESERVER_WORKERS', 10))