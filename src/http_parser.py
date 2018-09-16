class RedefinedHeaderKey(Exception):
    pass

def parse_http_request_line(request_line):
    method, request_uri, http_version = request_line.split(" ")
    return {
        "method": method,
        "request_uri": request_uri,
        "http_version": http_version
    }

def parse_http(text):
    lines = text.splitlines()
    parsed_message = parse_http_request_line(lines[0])
    parsed_message["headers"] = {}
    for i, line in zip(range(1,len(lines[1:]) + 1), lines[1:]):
        if line == "":
            break
        header_key, header_value = line.split(": ")
        if header_key in parsed_message:
            raise RedefinedHeaderKey(header_key)
        parsed_message["headers"][header_key] = header_value
    body_start = i + 1
    body = "\n".join(lines[body_start:])
    parsed_message["body"] = body
    return parsed_message

