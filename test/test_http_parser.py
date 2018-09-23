import os
from .http_examples import http_examples
from src.mainserver.http_parser import parse_http
def test_http_parser():
    for example in http_examples:
        assert(example[1] == parse_http(example[0]))

