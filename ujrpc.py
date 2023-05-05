import ujson as json

class JRPC2_ERRS: # see https://www.jsonrpc.org/specification;
    PARSE_ERR = {"code": -32700, "message": "Parse error"}
    INVLD_REQ = {"code": -32600, "message": "Invalid Request"}
    MTHD_NA   = {"code": -32601, "message": "Method not found"}
    INVLD_PRM = {"code": -32602, "message": "Invalid params"}
    INTNL_ERR = {"code": -32603, "message": "Internal error"}
    CUSTM_ERR = {"code": -32000, "message": "implementation-defined errors"} #-32000 ~ -32099

class JRPCException(Exception):
    def __init__(self, message, code, data):
        super(JRPCException, self).__init__(message)
        # Custom data
        self.message = message
        self.code = code
        self.data = data

class JRPCService:
    def __init__(self, method_map=None, api_version=0, debug=False):
        if method_map is None:
            self.method_map = {}
        else:
            self.method_map = method_map
        self.api_version = api_version
        self.doc_map = {}
        self.rsp2 = {'jsonrpc':"2.0"}
        self.debug = debug
    
    def add_method(self, name, method):
        self.method_map[name] = method

    def add_doc(self, name, doc):
        self.doc_map[name] = doc
    
    def handle_rpc(self, data, request):
        try:
            json_version, method_id, method = data["jsonrpc"], data["id"], data["method"]
        except KeyError:
            return self.rsp2|{'id': None, "error": JRPC2_ERRS.INVLD_REQ}
        # params must be abesent, list or dict, see Sepc section 4.2
        kwargs = {} ; args = []
        _parms = data.get("params")
        if isinstance(_parms, list):
            args = _parms
        elif isinstance(_parms, dict):
            kwargs = _parms
        if self.debug:
            print("params:", _parms)

        if json_version != "2.0":
            return self.rsp2|{'id': None, "error": JRPC2_ERRS.INVLD_REQ,}

        try:
            jfn = self.method_map[method]
        except KeyError:
            return self.rsp2|{'id': method_id, "error": JRPC2_ERRS.MTHD_NA,}

        try:
            ret = jfn( request, *args, **kwargs)
            return self.rsp2|{'id': method_id, 'result': ret}
        except JRPCException as ex:
            if self.debug:
                print("RPC.CUSTM_ERR", ex)
            return self.rsp2|{'id': method_id, "error": {"code": ex, "message": ex.message, "data": ex.data},}
        except TypeError as ex:
            if self.debug:
                print("RPC.INVLD_PRM", ex)
            return self.rsp2|{'id': None, "error": JRPC2_ERRS.INVLD_PRM}
        except Exception as ex:
            if self.debug:
                print("RPC.JRPC_Error", ex)
                #import usys; usys.print_exception(ex)
                return self.rsp2|{'id': method_id, "error": {"code": ex.errno, "message": ex.value, "data": ex.args}} # type:ignore
            else:
                return self.rsp2|{'id': None, "error": JRPC2_ERRS.INTNL_ERR}

    def __call__(self, request):
        try:
            data = json.loads(request) if isinstance(request, str) else request
            if isinstance(data, dict):
                return json.dumps(self.handle_rpc(data, request))
            elif isinstance(data, list):
                rets = []
                for batched_rpc in data:
                    rets.append(self.handle_rpc(batched_rpc, request))
                return json.dumps(rets)
            data = 1/0
        except Exception as ex:
            if self.debug:
                print("RPC.PARSE_ERR", ex, request)
            return json.dumps(self.rsp2|{'id': None, "error": JRPC2_ERRS.PARSE_ERR,})
    
    def api(self):
        desc = {}
        if self.api_version > 0:
            desc['api_version']=self.api_version
        desc['methods']={}
        for k in self.method_map:
            v = self.method_map[k]
            desc['methods'][k] = {}
            if k in self.doc_map:
                desc['methods'][k]['doc'] = self.doc_map[k]
            # inspect is available from micropython-lib if really needed
            # desc['methods'][k]['def'] = inspect.getargspec(v)
        return desc

def jsonremote(service, name=None, doc=None):
    def remotify(func):
        if isinstance(service, JRPCService):
            func_name = name
            if func_name is None:
                func_name = func.__name__
            service.add_method(func_name, func)
            if doc:
                service.add_doc(func_name, doc)
        else:
            raise NotImplementedError('"%s" not JRPCService instance' % str(service))
        return func

    return remotify
