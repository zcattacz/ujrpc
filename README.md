ujrpc 
=============

Adapted from [SimpleJsonRpc](https://github.com/moritz-wundke/simplejsonrpc) , tested on Micropython ESP32.

Changes:
----
- adapted for micropython
- fix handling of error, parameter and batched request
- shorten code to save space


Simple JSON-RPC 2.0 compilant middleware for python using decorators. With just a few lines of code you get a JSONRPC 2.0 compilant web API running and ready for your needs!

Install
----

copy ujrpc.py to micropython:

```sh
mpremote fs cp ujrpc.py :/
```

Usage
----

Just create a service class to store your API calls and decorate your methods:

```python
from ujrpc import JRPCService

jrpc = JRPCService(api_version=1)

# jrpc.debug = False

@jsonremote(jrpc, name='add', doc='test1: add')
def add(r, a, b):
    return a + b

@jsonremote(jrpc, name='echo', doc='test2: echo')
def echo(r, msg):
    return msg

@jsonremote(jrpc, name='login', doc='Method used to log a user in')
def login(request, user_name, user_pass):
    (...)

requests = """[
{"jsonrpc": "2.0",  "method": "add", "params": [11,22], "id": 1},
{"jsonrpc": "2.0",  "method": "echo", "params": ["Hello"], "id": 2},
]"""

# in mqtt_as callbacks or picoweb route handlers:
response = jrpc(requests)

print(response)
# [{"jsonrpc": "2.0", "id": 1, "result": 33}, 
#  {"jsonrpc": "2.0", "id": 2, "result": "Hello"}]


```


License
----

The MIT License (MIT)

Copyright (c) 2014 Moritz Wundke

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

