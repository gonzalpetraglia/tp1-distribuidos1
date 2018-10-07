
def gen_http_response(status_code, status_code_message, datetime, body):
    http_response = 'HTTP/1.1 {} {}\r\n'.format(status_code, status_code_message) + \
                                    'Date: {}\r\n'.format(datetime)+\
                                    'Server: JSON-SERVER v1.0.0\r\n'+\
                                    'Content-Length: {}\r\n'.format(len(body))+\
                                    'Content-Type: application/json\r\n'+\
                                    'Connection: Closed\r\n\r\n'+\
                                    '{}'.format(body)
    return http_response