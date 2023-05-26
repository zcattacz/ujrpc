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
        self.bind_self = None

    def _hndl_chk(self, data):
        try:
            v, mtd_id, mtd = data["jsonrpc"], data["id"], data["method"]
        except KeyError:
            return self.rsp2|{'id': None, "error": JRPC2_ERRS.INVLD_REQ}
        
        if v != "2.0":
            return self.rsp2|{'id': None, "error": JRPC2_ERRS.INVLD_REQ,}

        # params must be abesent, list or dict, see Sepc section 4.2
        kwargs = {} ; args = []
        _parms = data.get("params")
        if _parms is None:
            pass
        elif isinstance(_parms, list):
            args = _parms
        elif isinstance(_parms, dict):
            kwargs = _parms
        else:
            return self.rsp2|{'id': None, "error": JRPC2_ERRS.INVLD_PRM}
        
        if self.debug:
            print("params:", _parms)

        try:
            return {"method":self.method_map[mtd], "id":mtd_id, "args":args, "kwargs":kwargs}
        except KeyError:
            return self.rsp2|{'id': mtd_id, "error": JRPC2_ERRS.MTHD_NA,}
        
    def _hndl_err(self, ex, ctx):
        if isinstance(ex,JRPCException):
            if self.debug:
                print("RPC.CUSTM_ERR", ex)
            return self.rsp2|{'id': ctx["id"], "error": {"code": ex, "message": ex.message, "data": ex.data},}
        elif isinstance(ex,TypeError):
            if self.debug:
                print("RPC.INVLD_PRM", ex)
            return self.rsp2|{'id': None, "error": JRPC2_ERRS.INVLD_PRM}
        else:
            if self.debug:
                print("RPC.JRPC_Error", ex)
                #import usys; usys.print_exception(ex)
                return self.rsp2|{'id': ctx["id"], "error": {"code": ex.errno, "message": ex.value, "data": ex.args}} # type:ignore
            else:
                return self.rsp2|{'id': None, "error": JRPC2_ERRS.INTNL_ERR}

    def _hndl_rpc(self, data):
        ctx = self._hndl_chk(data)
        if "jsonrpc" in ctx: return ctx
        _self = self.bind_self if self.bind_self else self
        
        try:
            ret = ctx["method"](_self, *ctx["args"], **ctx["kwargs"]) # type:ignore
            return self.rsp2|{'id': ctx["id"], 'result': ret}
        except Exception as ex:
            return self._hndl_err(ex, ctx)

    async def _hndl_rpca(self, data):
        ctx = self._hndl_chk(data)
        if "jsonrpc" in ctx: return ctx
        _self = self.bind_self if self.bind_self else self
        
        try:
            if ctx["method"].__class__.__name__ == "generator": #async function
                ret = await ctx["method"](_self, *ctx["args"], **ctx["kwargs"]) #type:ignore
            else:
                ret = ctx["method"](_self, *ctx["args"], **ctx["kwargs"]) #type:ignore
            return self.rsp2|{'id': ctx["id"], 'result': ret}
        except Exception as ex:
            return self._hndl_err(ex, ctx)

    def handle_rpc(self, request):
        try:
            data = json.loads(request) if isinstance(request, str) else request
            if isinstance(data, dict):
                return json.dumps(self._hndl_rpc(data))
            elif isinstance(data, list):
                rets = []
                for batched_rpc in data:
                    rets.append(self._hndl_rpc(batched_rpc))
                return json.dumps(rets)
            data = 1/0
        except Exception as ex:
            if self.debug:
                print("RPC.PARSE_ERR", ex, request)
            return json.dumps(self.rsp2|{'id': None, "error": JRPC2_ERRS.PARSE_ERR,})
    
    async def handle_rpca(self, request):
        try:
            data = json.loads(request) if isinstance(request, str) else request
            if isinstance(data, dict):
                return json.dumps(await self._hndl_rpca(data))
            elif isinstance(data, list):
                rets = []
                for batched_rpc in data:
                    rets.append(await self._hndl_rpca(batched_rpc))
                return json.dumps(rets)
            data = 1/0
        except Exception as ex:
            if self.debug:
                print("RPC.PARSE_ERR", ex, request)
            return json.dumps(self.rsp2|{'id': None, "error": JRPC2_ERRS.PARSE_ERR})

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

    def fn(self, name=None, doc=None):
        def remotify(func):
            if self.debug:
                print("remotify:", func, func.__name__)
            func_name = name
            if func_name is None:
                func_name = func.__name__
            self.method_map[func_name] = func
            if doc:
                self.doc_map[func_name] = doc
            return func

        return remotify
