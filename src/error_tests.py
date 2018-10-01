import requests
import socket
import json

PORT = 8080
HOST = 'localhost'
PREFIX = 'http://{}:{}'.format(HOST, PORT)

def invalid_uri_post():
    resp = requests.post(PREFIX + '/', json={"ok": "ok"})
    assert (resp.status_code == 400)
    assert (resp.json()['status'] == 'invalid_uri')
    resp = requests.post(PREFIX + '/not_ok', json={"ok": "ok"})
    assert (resp.status_code == 400)
    assert (resp.json()['status'] == 'invalid_uri')
    resp = requests.post(PREFIX + '/not_ok/not_ok/not_ok', json={"ok": "ok"})
    assert (resp.status_code == 400)
    assert (resp.json()['status'] == 'invalid_uri')

def invalid_uri_get():
    resp = requests.get(PREFIX + '/')
    assert (resp.status_code == 400)
    assert (resp.json()['status'] == 'invalid_uri')
    resp = requests.get(PREFIX + '/not_ok')
    assert (resp.status_code == 400)
    assert (resp.json()['status'] == 'invalid_uri')
    resp = requests.get(PREFIX + '/not_ok/not_ok')
    assert (resp.status_code == 400)
    assert (resp.json()['status'] == 'invalid_uri')

def invalid_uri_put():
    resp = requests.put(PREFIX + '/', json={"ok": "ok"})
    assert (resp.status_code == 400)
    assert (resp.json()['status'] == 'invalid_uri')
    resp = requests.put(PREFIX + '/not_ok', json={"ok": "ok"})
    assert (resp.status_code == 400)
    assert (resp.json()['status'] == 'invalid_uri')
    resp = requests.put(PREFIX + '/not_ok/not_ok', json={"ok": "ok"})
    assert (resp.status_code == 400)
    assert (resp.json()['status'] == 'invalid_uri')

def invalid_uri_delete():
    resp = requests.delete(PREFIX + '/')
    assert (resp.status_code == 400)
    assert (resp.json()['status'] == 'invalid_uri')
    resp = requests.delete(PREFIX + '/not_ok')
    assert (resp.status_code == 400)
    assert (resp.json()['status'] == 'invalid_uri')
    resp = requests.delete(PREFIX + '/not_ok/not_ok')
    assert (resp.status_code == 400)
    assert (resp.json()['status'] == 'invalid_uri')

def body_missing():
    resp = requests.post(PREFIX + '/ok/ok/id')
    assert (resp.status_code == 400)
    assert (resp.json()['status'] == 'missing_body')
    resp = requests.put(PREFIX + '/ok/ok/id')
    assert (resp.status_code == 400)
    assert (resp.json()['status'] == 'missing_body')

def body_not_json():
    resp = requests.post(PREFIX + '/ok/ok', data='Not json body')
    assert (resp.status_code == 400)
    assert (resp.json()['status'] == 'body_not_json')
    resp = requests.put(PREFIX + '/ok/ok/id', data='Not json body')
    assert (resp.status_code == 400)
    assert (resp.json()['status'] == 'body_not_json')

def method_not_supported():
    resp = requests.options(PREFIX + '/ok/ok/id')
    assert (resp.status_code == 400)
    assert (resp.json()['status'] == 'method_not_supported')

def header_too_long():
    http_request = 'POST /ok/ok HTTP/1.1\r\n'+ \
        'User-Agent: Mozilla/4.0 (compatible; MSIE5.01; Windows NT)\r\n'+ \
        'Host: www.tutorialspoint.com\r\n'
    
    for i in range(1000):
        http_request += 'Accept-Language{}: en-us\r\n'.format(i)

    http_request += 'Accept-Encoding: gzip, deflate\r\n'+ \
        'Connection: Keep-Alive\r\n'+ \
        '\r\n'

    s = socket.socket()
    s.connect((HOST, PORT))
    s.sendall(http_request.encode())
    headers, body = s.recv(4096).decode().split('\r\n\r\n')
    status_code = int(headers.splitlines()[0].split(' ')[1])
    response = json.loads(body)

    assert (status_code == 400)
    assert (response['status']  == 'header_too_long')

def redefined_header_key():
    http_request = 'GET /ok/ok/id HTTP/1.1\r\n'+ \
        'User-Agent: Mozilla/4.0 (compatible; MSIE5.01; Windows NT)\r\n'+ \
        'Host: www.tutorialspoint.com\r\n'+ \
        'Accept-Language: en-us\r\n'+ \
        'Accept-Encoding: gzip, deflate\r\n'+ \
        'Accept-Encoding: gzip, deflate\r\n'+ \
        'Connection: Keep-Alive\r\n'+ \
        '\r\n'

    s = socket.socket()
    s.connect((HOST, PORT))
    s.sendall(http_request.encode())
    headers, body = s.recv(4096).decode().split('\r\n\r\n')
    status_code = int(headers.splitlines()[0].split(' ')[1])
    response = json.loads(body)
    assert (status_code == 400)
    assert (response['status']  == 'redefined_header_key')   

def timeout():
    http_request = 'GET /ok/ok/id HTTP/1.1 EXTRA\r\n'+ \
        'User-Agent: Mozilla/4.0 (compatible; MSIE5.01; Windows NT)\r\n'+ \
        'Host: www.tutorialspoint.com\r\n'+ \
        'Accept-Language: en-us\r\n'

    s = socket.socket()
    s.connect((HOST, PORT))
    s.sendall(http_request.encode())
    headers, body = s.recv(4096).decode().split('\r\n\r\n')
    status_code = int(headers.splitlines()[0].split(' ')[1])
    response = json.loads(body)
    assert (status_code == 400)
    assert (response['status']  == 'timedout')
    
def malformed_request_line():
    http_request = 'GET /ok/ok/id HTTP/1.1 EXTRA\r\n'+ \
        'User-Agent: Mozilla/4.0 (compatible; MSIE5.01; Windows NT)\r\n'+ \
        'Host: www.tutorialspoint.com\r\n'+ \
        'Accept-Language: en-us\r\n'+ \
        'Accept-Encoding: gzip, deflate\r\n'+ \
        'Connection: Keep-Alive\r\n'+ \
        '\r\n'

    s = socket.socket()
    s.connect((HOST, PORT))
    s.sendall(http_request.encode())
    headers, body = s.recv(4096).decode().split('\r\n\r\n')
    status_code = int(headers.splitlines()[0].split(' ')[1])
    response = json.loads(body)
    assert (status_code == 400)
    assert (response['status']  == 'malformed_request_line')
    
    http_request = 'GET /ok/ok/id\r\n'+ \
        'User-Agent: Mozilla/4.0 (compatible; MSIE5.01; Windows NT)\r\n'+ \
        'Host: www.tutorialspoint.com\r\n'+ \
        'Accept-Language: en-us\r\n'+ \
        'Accept-Encoding: gzip, deflate\r\n'+ \
        'Connection: Keep-Alive\r\n'+ \
        '\r\n'

    s = socket.socket()
    s.connect((HOST, PORT))
    s.sendall(http_request.encode())
    headers, body = s.recv(4096).decode().split('\r\n\r\n')
    status_code = int(headers.splitlines()[0].split(' ')[1])
    response = json.loads(body)
    assert (status_code == 400)
    assert (response['status']  == 'malformed_request_line')
    
def body_too_long():
    http_request = 'POST /ok/ok HTTP/1.1\r\n'+ \
        'User-Agent: Mozilla/4.0 (compatible; MSIE5.01; Windows NT)\r\n'+ \
        'Host: www.tutorialspoint.com\r\n'+ \
        'Accept-Language: en-us\r\n'+ \
        'Accept-Encoding: gzip, deflate\r\n'+ \
        'Connection: Keep-Alive\r\n'+ \
        'Content-Type: application/json\r\n' + \
        'Content-Length: {}\r\n'.format(str(2**56)) + \
        '\r\n'

    s = socket.socket()
    s.connect((HOST, PORT))
    s.sendall(http_request.encode())
    headers, body = s.recv(4096).decode().split('\r\n\r\n')
    status_code = int(headers.splitlines()[0].split(' ')[1])
    response = json.loads(body)
    assert (status_code == 400)
    assert (response['status']  == 'body_too_long')

    http_request = 'PUT /ok/ok/ok HTTP/1.1\r\n'+ \
        'User-Agent: Mozilla/4.0 (compatible; MSIE5.01; Windows NT)\r\n'+ \
        'Host: www.tutorialspoint.com\r\n'+ \
        'Accept-Language: en-us\r\n'+ \
        'Accept-Encoding: gzip, deflate\r\n'+ \
        'Connection: Keep-Alive\r\n'+ \
        'Content-Type: application/json\r\n' + \
        'Content-Length: {}\r\n'.format(str(2**56)) + \
        '\r\n'

    s = socket.socket()
    s.connect((HOST, PORT))
    s.sendall(http_request.encode())
    headers, body = s.recv(4096).decode().split('\r\n\r\n')
    status_code = int(headers.splitlines()[0].split(' ')[1])
    response = json.loads(body)
    assert (status_code == 400)
    assert (response['status']  == 'body_too_long')
    
def cutted_body():
    body_send = 'too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_too_long_body_body'
    http_request = 'POST /ok/ok HTTP/1.1\r\n'+ \
        'User-Agent: Mozilla/4.0 (compatible; MSIE5.01; Windows NT)\r\n'+ \
        'Host: www.tutorialspoint.com\r\n'+ \
        'Accept-Language: en-us\r\n'+ \
        'Accept-Encoding: gzip, deflate\r\n'+ \
        'Connection: Keep-Alive\r\n'+ \
        'Content-Type: application/json\r\n' + \
        'Content-Length: 4\r\n' + \
        '\r\n' + \
        '{}'.format(body_send)

    s = socket.socket()
    s.connect((HOST, PORT))
    s.sendall(http_request.encode())
    headers, body = s.recv(4096).decode().split('\r\n\r\n')
    status_code = int(headers.splitlines()[0].split(' ')[1])
    response = json.loads(body)
    assert (status_code == 201)
    assert (response['status']  == 'ok')
    _id = response['id']
    response = requests.get(PREFIX + '/' + _id).text
    assert ( 4 <= len(response) < len(body_send) )

invalid_uri_delete()
invalid_uri_post()
invalid_uri_put()
invalid_uri_get()
body_missing()
body_not_json()
method_not_supported()
redefined_header_key()
header_too_long()
body_too_long()
malformed_request_line()
cutted_body()
timeout()
