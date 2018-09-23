http_examples = [
    (
        'GET /hello.htm HTTP/1.1\n'+
        'User-Agent: Mozilla/4.0 (compatible; MSIE5.01; Windows NT)\n'+
        'Host: www.tutorialspoint.com\n'+
        'Accept-Language: en-us\n'+
        'Accept-Encoding: gzip, deflate\n'+
        'Connection: Keep-Alive\n'+
        '\n',
        {
            "method": "GET",
            "request_uri": "/hello.htm",
            "http_version": "HTTP/1.1",
            "headers": {
                'user-agent': 'Mozilla/4.0 (compatible; MSIE5.01; Windows NT)',
                'host': 'www.tutorialspoint.com',
                'accept-language': 'en-us',
                'accept-encoding': 'gzip, deflate',
                'connection': 'Keep-Alive'
            },
            "body": ""
        }),
    (
        'GET /t.html HTTP/1.1\n'+
        'User-Agent: Mozilla/4.0 (compatible; MSIE5.01; Windows NT)\n'+
        'Host: www.tutorialspoint.com\n'+
        'Accept-Language: en-us\n'+
        'Accept-Encoding: gzip, deflate\n'+
        'Connection: Keep-Alive\n'+
        '\n',
        {
            "method": "GET",
            "request_uri": "/t.html",
            "http_version": "HTTP/1.1",
            "headers": {
                'user-agent': 'Mozilla/4.0 (compatible; MSIE5.01; Windows NT)',
                'host': 'www.tutorialspoint.com',
                'accept-language': 'en-us',
                'accept-encoding': 'gzip, deflate',
                'connection': 'Keep-Alive'
            },
            "body": ""
        }
    ),
    (
        'GET /hello.htm?limit=30&start=40 HTTP1\n'+
        'User-Agent: Mozilla/4.0 (compatible; MSIE5.01; Windows NT)\n'+
        'Host: www.tutorialspoint.com\n'+
        'Accept-Language: en-us\n'+
        'Accept-Encoding: gzip, deflate\n'+
        'Connection: Keep-Alive\n',
        {
            "method": "GET",
            "request_uri": "/hello.htm?limit=30&start=40",
            "http_version": "HTTP1",
            "headers": {
                'user-agent': 'Mozilla/4.0 (compatible; MSIE5.01; Windows NT)',
                'host': 'www.tutorialspoint.com',
                'accept-language': 'en-us',
                'accept-encoding': 'gzip, deflate',
                'connection': 'Keep-Alive'
            },
            "body": ""
        }

    )
]