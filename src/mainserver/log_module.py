import os
import logging
import traceback
from configs import LOGFILE, LOG_LEVEL, LOG_FORMAT
import logging

logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger('mainserver')
logger.setLevel(LOG_LEVEL)

def log_loop(logs_queue):
    os.makedirs(os.path.dirname(LOGFILE), exist_ok=True)
    logger.info('Going to log into {}'.format(LOGFILE))
    with open(LOGFILE, 'a') as logfile:
        while True:
            try:
                log_dict = logs_queue.get()
                method = log_dict['method']
                request_uri = log_dict['request_uri']
                status_code = log_dict['status_code']
                request_datetime = log_dict['request_datetime']
                address = log_dict['address']

                logfile.write("{} {} {} {} {}\n".format(method, request_uri, status_code, request_datetime, address))
                logfile.flush()
            except Exception:
                logger.error(traceback.format_exc())
