import socket
import time
from multiprocessing import Process, Queue, Manager
import logging
import os
from config import NUMBER_OF_RESPONDERS, NUMBER_OF_PROCESSERS, REQUESTS_PORT, RESPONSES_PORT, RESPONSES_SOCKET_LENGTH, REQUESTS_SOCKET_LENGTH
from http_processer import http_process
from http_responder import http_respond
from log_module import log_loop

FORMAT = "%(asctime)-15s %(process)d %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('mainserver')
logger.setLevel(logging.DEBUG)
logger.info("Mainserver is up and running :)")

if __name__ == "__main__":
    accepted_clients_queue = Queue()
    logs_queue = Queue()



    fileserver_responses_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    fileserver_responses_socket.bind(('0.0.0.0', RESPONSES_PORT))
    fileserver_responses_socket.listen(RESPONSES_SOCKET_LENGTH)


    processers = [Process(target=http_process, args=(accepted_clients_queue,)) for i in range(NUMBER_OF_PROCESSERS)]
    responders = [Process(target=http_respond, args=(fileserver_responses_socket, logs_queue,)) for i in range(NUMBER_OF_RESPONDERS)]
    logger_process = Process(target=log_loop, args=(logs_queue,))

    logger.info("Going to start {} processers and {} responders ".format(NUMBER_OF_PROCESSERS, NUMBER_OF_RESPONDERS))

    for processer in processers:
        processer.start()
    for responder in responders:
        responder.start()
    logger_process.start()


    incoming_clients_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    incoming_clients_socket.bind(('0.0.0.0', REQUESTS_PORT))
    incoming_clients_socket.listen(REQUESTS_SOCKET_LENGTH)

    while True:
        logger.debug('Listening for more clients')

        accepted_client = incoming_clients_socket.accept()
        logger.info('Accepted new client')
        accepted_clients_queue.put(accepted_client)

    for processer in processers:
        processer.join()
    for responder in responders:
        responder.join()
    logger_process.join()

