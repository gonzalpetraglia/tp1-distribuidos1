import os
import logging
import traceback
from configs import LOGFILE, LOG_LEVEL, LOG_FORMAT
import logging
import signal

logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger('mainserver')
logger.setLevel(LOG_LEVEL)

def log_loop(logs_queue):
    os.makedirs(os.path.dirname(LOGFILE), exist_ok=True)
    logger.debug('Going to log into {}'.format(LOGFILE))
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)

    with open(LOGFILE, 'a') as logfile:
        finish = False
        while not finish:
            try:
                message = logs_queue.get()
                logger.debug('Logger received {}'.format(message))
                if message == 'END':
                    finish = True
                else: 
                    log_dict = message
                    method = log_dict['method']
                    request_uri = log_dict['request_uri']
                    status_code = log_dict['status_code']
                    request_datetime = log_dict['request_datetime']
                    address = log_dict['address']

                    logfile.write("{} {} {} {} {}\n".format(method, request_uri, status_code, request_datetime, address))
                    logfile.flush()
                    logger.info('Logged (audit)')
            except Exception:
                logger.error(traceback.format_exc())
        

        logger.info('Stopped logging')
