ujrpc 
=============

Adapted from [SimpleJsonRpc](https://github.com/moritz-wundke/simplejsonrpc) , tested on Micropython ESP32, ESP32-S2, CPython 3.9

Changes:
----
- adapted for micropython
- fix handling of error, parameter and batched request
- shorten code to save space
- add asyncio support
- removed __call__(), use handle_rpc(request)/handle_rpca(request) instead

Simple JSON-RPC 2.0 compilant middleware for python using decorators. With just a few lines of code you get a JSONRPC 2.0 compilant web API running and ready for your needs!

Install on Micropython
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

@jrpc.fn(name='add', doc='test1: add')
def add(r, a, b):
    return a + b

@jrpc.fn(name='echo', doc='test2: echo')
def echo(r, msg):
    return msg

@jrpc.fn(name='login', doc='Method used to log a user in')
def login(r, user_name, user_pass):
    (...)

requests = """[
{"jsonrpc": "2.0",  "method": "add", "params": [11,22], "id": 1},
{"jsonrpc": "2.0",  "method": "echo", "params": ["Hello"], "id": 2},
]"""

# in mqtt_as callbacks or picoweb route handlers:
response = jrpc.handle_rpc(requests)

print(response)
# [{"jsonrpc": "2.0", "id": 1, "result": 33}, 
#  {"jsonrpc": "2.0", "id": 2, "result": "Hello"}]

try:
    import uasyncio as asyncio
except:
    import asyncio

class TestAsync():
    def __init__(self):
        self.cal_cnt = 0
    @jrpc.fn(name="async_add")
    async def add(self, a, b):
        self.cal_cnt += 1
        return a+b
    @jrpc.fn(name="product")
    def prd(self, a, b):
        self.cal_cnt += 1
        return a*b

requests = """[
{"jsonrpc": "2.0",  "method": "async_add", "params": [11,22], "id": 1},
{"jsonrpc": "2.0",  "method": "product", "params": [33,44], "id": 2},
]"""
async def main():
    ta = TestAsync()
    jrpc.bind_self = ta # pass ta as 1st parameter to decorated fn, instead of jrpc
    print("cal_cnt=", ta.cal_cnt)
    response = await jrpc.handle_rpca(requests)
    print(response)
    print("cal_cnt=", ta.cal_cnt)

asyncio.run(main())

# cal_cnt= 0
# [{"jsonrpc": "2.0", "id": 1, "result": 33}, {"jsonrpc": "2.0", "id": 2, "result": 1452}]
# cal_cnt= 2

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

