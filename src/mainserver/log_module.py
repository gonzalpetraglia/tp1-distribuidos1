import os
import logging
import traceback
from config import LOGFILE


FORMAT = "%(asctime)-15s %(process)d %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('mainserver')
logger.setLevel(logging.DEBUG)

def log_loop(logs_queue):
    os.makedirs(os.path.dirname(LOGFILE), exist_ok=True)
    with open(LOGFILE, 'a') as logfile:
        while True:
            try:
                log_dict = logs_queue.get()
                method = log_dict['method']
                request_uri = log_dict['request_uri']
                status_code = log_dict['status_code']

                logfile.write("{} {} {}\n".format(method, request_uri, status_code))
                logfile.flush()
            except Exception:
                logger.error(traceback.format_exc())
