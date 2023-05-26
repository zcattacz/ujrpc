from ujrpc import JRPCService, JRPCException
import json
try:
    from typing import Dict, Union
except:
    pass

try:
    import uasyncio as asyncio
except:
    import asyncio

jrpc = JRPCService(api_version=1)
jrpc.debug = False
jrpc.ret_str = False

def req(parameters, params=None, id=0, jstr=False) -> Union[str,Dict]:
    req = {"jsonrpc": "2.0", 
           "method": parameters, 
           "id": id+1}
    if params:
        req["params"] = params
    return json.dumps(req) if jstr else req

# test 1st param "r" is jrpc
@jrpc.fn()
def test_self(self):
    return self

# test paramters
@jrpc.fn()
def test_args(r, a, b):
    return a+b

@jrpc.fn()
def test_kwargs(r, a=0, b=0):
    return a+b

@jrpc.fn()
def test_no_params(r):
    return 100



tests = {}
tests["test_self"] = [
    # fnc_name, params, checks[(key, value),...]
    ["test_self", None, [("result", jrpc)]]
]
_100 = [("result", 100)]
tests["params test"] = [
    ["test_args", [1,2], [("result", 3)]],
    ["test_kwargs", {"a":1,"b":2}, [("result", 3)]],
    ["test_no_params", None, _100]
]
_e1 = [("error.message", "Invalid params")]
_3 = [("result", 3)]
tests["invalid params test"] = [
    ["test_no_params",[1], _e1], #" excessive params"
    ["test_args",[1], _e1], # less params
    ["test_args",[1,2,3], _e1], # more params
    ["test_args",{"a":1, "b":2}, _3], # mismatch params
    ["test_args",{"b":2, "a":1}, _3], # mismatch params
    ["test_args",{"b":1}, _e1], # mismatch params
]


_0 = [("result", 0)]
tests["empty params test"] = [
    ["test_kwargs",[], _0],
    ["test_kwargs",{}, _0],
    ["test_kwargs",None, _0],
    ["test_no_params",None, _100],
    ["test_args",[], _e1],
]

tests["non-structured params test"] = [
    ["test_args","123", _e1],
    ["test_kwargs","123", _e1],
    ["test_args",123, _e1],
    ["test_kwargs",123, _e1],
]

tests["non-structured params test"] = [
    ["test_args","123", _e1],
    ["test_kwargs","123", _e1],
    ["test_args",123, _e1],
    ["test_kwargs",123, _e1],
]

_e2 = [("error.message",'Method not found')]
# should check method existence before validating paramter
tests["methord test"] = [
    ["test_not_found_method",None, _e2],
    ["test_not_found_method",{"a":1,"d":22}, _e2],
]

def test_rpc_error(tests, test_async=False):
    for test_group, tests in tests.items():
        print(f"Testing {test_group}")
        for test in tests:
            method_name, parameters, checks = test
            if parameters:
                if test_async:
                    ret = asyncio.run(jrpc.handle_rpca(req(method_name,parameters)))
                else:
                    ret = jrpc.handle_rpc(req(method_name,parameters))
            else:
                if test_async:
                    ret = asyncio.run(jrpc.handle_rpca(req(method_name)))
                else:
                    ret = jrpc.handle_rpc(req(method_name))
            for ck in checks: # check values in response
                keys = ck[0].split(".")
                v = ret
                for k in keys:
                    v = v[k]
                try:
                    assert(v == ck[1])
                except AssertionError as ex:
                    print(f"  Method: {method_name}, Param:{parameters}")
                    print(f"  Expecting {ck[0]} == {ck[1]}, but got {v}")

def test_parser_error(test_async=False):
    # test json error
    for s in ["dsfsdfds}ew223}", "{123}}", "self"]:
        q = req("test_args", 123, jstr=True).replace("123",s)
        if test_async:
            ret:dict = asyncio.run(jrpc.handle_rpca(q))
        else:
            ret:dict = jrpc.handle_rpc(q)
        assert(ret["error"]["message"] == "Parse error")
        #assert(ret1["error"]["message"] == 'Invalid params')

#test for batched RPC"
req1 = """[
{"jsonrpc": "2.0",  "method": "test_args", "params": {}, "id": 1},
{"jsonrpc": "2.0",  "method": "test_kwargs", "params": ["Hello"], "id": 2},
{"jsonrpc": "2.0",  "method": "test_no_params", "params": ["Hello"], "id": 3},
{"jsonrpc": "2.0",  "method": "test_args", "params": [11,22], "id": 4},
{"jsonrpc": "2.0",  "method": "test_kwargs", "params": {"a":1,"b":2}, "id": 5},
{"jsonrpc": "2.0",  "method": "test_no_params", "params": {}, "id": 6},
]"""

def test_batched_request(test_async=False):
    if test_async:
        ret:dict = asyncio.run(jrpc.handle_rpca(req1))
    else:
        ret:dict = jrpc.handle_rpc(req1)
    assert(type(ret) == list and len(ret) == 6)
    for i in range(0,3):
        assert(ret[i]["error"]["message"] == 'Invalid params')
    for i, v in enumerate([33,3,100]):
        assert(ret[i+3]["result"] == v)



for test_async in [True, False]:
    print(f"{'=== handle_rpca() ===' if test_async else '=== handle_rpc() ==='}")
    test_rpc_error(tests, test_async=test_async)
    test_parser_error(test_async=test_async)
    test_batched_request(test_async=test_async)
