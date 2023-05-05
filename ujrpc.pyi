# -*- coding: utf-8 -*-
"""
Simple jsonrpc base implementation using decorators.

    from urjpc import *

    loginservice = ujrpc(api_version=1)

    @jsonremote(loginservice, name='login', doc='Method used to log a user in')
    def login(request, user_name, user_pass):
        (...)
"""

from typing import Union, Optional, Any, Callable
TFunc = Callable[..., Any]

class JRPC2_ERRS:
    """
    see https://www.jsonrpc.org/specification
    custom error from -32000 ~ -32099
    """
    PARSE_ERR = {"code": -32700, "message": "Parse error"}
    INVLD_REQ = {"code": -32600, "message": "Invalid Request"}
    MTHD_NA   = {"code": -32601, "message": "Method not found"}
    INVLD_PRM = {"code": -32602, "message": "Invalid params"}
    INTNL_ERR = {"code": -32603, "message": "Internal error"}
    CUSTM_ERR = {"code": -32000, "message": "implementation-defined errors"}

class JRPCException(Exception):
    """
    Base exception class for program specific errors
    """
    def __init__(self, message:str, code:int, data:Any):
        # Custom data
        self.message = message
        self.code = code
        self.data = data

class JRPCService:
    """
    Simple JSON RPC service
    """
    def __init__(self, method_map:Optional[dict]=None, api_version:Optional[int]=0, debug=False):
        self.method_map = {}
        self.api_version = api_version
        self.doc_map = {}
        self.rsp2 = {'jsonrpc':"2.0"}
        self.debug = debug
    
    def add_method(self, name:str, method:TFunc) -> None: ...
    def add_doc(self, name:str, doc:str) -> None: ...
    def handle_rpc(self, data: Union[list, dict], request:Union[str, list, dict]) -> dict: ...
    def __call__(self, request: Union[str, list, dict]) -> str: ...
    def api(self) -> str: ...

def jsonremote(service:JRPCService, name:Optional[str]=None, doc:Optional[str]=None)-> Callable[[TFunc], TFunc]:
    """
    makes JRPCSerivce a decorator so that you can write :
    
    from ujrpc import *

    loginservice = JRPCSerivce(api_version=1)

    @jsonremote(loginservice, name='login', doc='Method used to log a user in')
    def login(request, user_name, user_pass):
        (...)
    
    """
