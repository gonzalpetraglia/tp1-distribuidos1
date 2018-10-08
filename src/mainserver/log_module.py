import os
import logging
import traceback
import logging
import signal
from multiprocessing import Process

from configs import LOGFILE, LOG_LEVEL, LOG_FORMAT
from lib.encoder import END_TOKEN
logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger('mainserver')
logger.setLevel(LOG_LEVEL)

class AuditLogger(Process):
    def __init__(self,logs_queue):
        self.logs_queue = logs_queue
        super(AuditLogger, self).__init__()

    def run(self):
        os.makedirs(os.path.dirname(LOGFILE), exist_ok=True)
        logger.debug('Going to log into {}'.format(LOGFILE))
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        self._log_loop()

    def _log_loop(self):
        with open(LOGFILE, 'a') as logfile:
            finish = False
            while not finish:
                try:
                    message = self.logs_queue.get()
                    logger.debug('Logger received {}'.format(message))
                    if message == END_TOKEN:
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
