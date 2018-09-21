import socket
import time
from multiprocessing import Process
import http_parser
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind(('127.0.0.1', 8081))
s.listen(5)

def treat_get(parsed_msg):
	raise Exception('TODO')

def treat_post(parsed_msg):
	raise Exception('TODO')

def treat_put(parsed_msg):
	raise Exception('TODO')

def treat_delete(parsed_msg):
	raise Exception('TODO')

def treat_message(msg):
    parsed_msg = http_parser.parse_http(msg)
    
    method = parsed_msg['method']

    if method == "GET":
        treat_get(parsed_msg)
    elif method == "POST":
    	treat_post(parsed_msg)
    elif method == "PUT":
    	treat_put(parsed_msg)
    elif method == "DELETE":
    	treat_delete(parsed_msg)
    else:
    	raise Exception('WTF') # TODO

    return 'HTTP/1.1 200 OK\n' + \
                    'Date: Mon, 27 Jul 2009 12:28:53 GMT\n'+\
                    'Server: Apache/2.2.14 (Win32)\n'+\
                    'Last-Modified: Wed, 22 Jul 2009 19:15:56 GMT\n'+\
                    'Content-Length: 88\n'+\
                    'Content-Type: text/html\n'+\
                    'Connection: Closed\n\n'+\
                    parsed_msg['request_uri'] + '\n\n' +\
                    'Holaaaaaaaaaaa\n\n'\

def work():
    while True:
        c, addr = s.accept()
        chunk  = '' # TODO Dont have everything on memory
        breaks_found = 0

        # while breaks_found < 2:
        chunk += c.recv(2048)
            # breaks_found += chunk.count('\n\n') # TODO: Malformed requests?

        response = treat_message(chunk)
        c.send(response)
        c.close()

processes = [Process(target=work) for i in range(20)]

for process in processes:
    process.start()
    
for process in processes:
    process.join()


'\n\n\n\n\n\n'

