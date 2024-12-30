try:
    import ujson as json
    import uasyncio as asyncio
    is_mpy = True
except:
    import json
    import asyncio
    is_mpy = False

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
        self.rsp2 = {'jsonrpc':"2.0", "id":None}
        self.debug = debug
        self.bind_self = None
        self.ret_str = True

    def _hndl_chk(self, data, _r):
        try:
            v, mtd_id, mtd = data["jsonrpc"], data["id"], data["method"]
        except KeyError:
            _r.update({"error": JRPC2_ERRS.INVLD_REQ})
            return
        
        if v != "2.0":
            _r.update({"error": JRPC2_ERRS.INVLD_REQ})
            return
        
        try:
            mtd = self.method_map[mtd]
        except KeyError:
            _r.update({"error": JRPC2_ERRS.MTHD_NA})
            return

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
            _r.update({"error": JRPC2_ERRS.INVLD_PRM})
            return
        
        # `kwargs` is an extension to pass both positional and keyword arguments
        # this is not defined in JRPC2.0 Spec,
        _parms = data.get("kwargs")
        if _parms is not None:
            kwargs = _parms
        
        if self.debug:
            print("method:", mtd.__name__, "params:", _parms)

        _r["id"] = mtd_id
        return {"method":mtd, "id":mtd_id, "args":args, "kwargs":kwargs,
                "_self": self.bind_self if self.bind_self else self}
        
    def _hndl_err(self, ex, ctx, _r):
        if self.debug:
            print("RPC Handling Error", ex.args, type(ex))
        if isinstance(ex,JRPCException):
            _r.update({"error": {"code": ex.code, "message": ex.message, "data": ex.data}})
        elif isinstance(ex,TypeError):
            if not self.debug:
                _r["id"] = None
            _r.update({"error": JRPC2_ERRS.INVLD_PRM})
        else:
            if self.debug:
                # not all exception have .value/.errno on cpy
                _r.update({"error": {"type": type(ex), "args": str(ex.args), }}) # type:ignore
            else:
                _r["id"] = None
                _r.update({'id': None, "error": JRPC2_ERRS.INTNL_ERR})

    def _hndl_rpc1(self, data, _r):
        ctx = self._hndl_chk(data, _r)
        if ctx is None: return
        
        try:
            ret = ctx["method"](ctx["_self"], *ctx["args"], **ctx["kwargs"]) # type:ignore
            _r.update({'result': ret})
        except Exception as ex:
            self._hndl_err(ex, ctx, _r)

    async def _hndl_rpc1a(self, data, _r):
        ctx = self._hndl_chk(data, _r)
        if ctx is None: return
        
        try:
            is_async = False
            if is_mpy and ctx["method"].__class__.__name__ == "generator": #async function
                is_async = True
            elif (not is_mpy) and (asyncio.iscoroutinefunction(ctx["method"]) or hasattr(ctx["method"], "__await__")):
                is_async = True

            if is_async:
                ret = await ctx["method"](ctx["_self"], *ctx["args"], **ctx["kwargs"]) #type:ignore
            else:
                ret = ctx["method"](ctx["_self"], *ctx["args"], **ctx["kwargs"]) #type:ignore
            _r.update({'result': ret})
        except Exception as ex:
            self._hndl_err(ex, ctx, _r)

    def _hndl_parsing(self, request, _r):
        try:
            return json.loads(request) if isinstance(request, str) else request
        except Exception as ex:
            if self.debug:
                print("RPC.PARSE_ERR", ex, request)
            _r.update({"error": JRPC2_ERRS.PARSE_ERR})

    def handle_rpc(self, request):
        _r = self.rsp2.copy()
        data = self._hndl_parsing(request, _r)
        if isinstance(data, dict):
            self._hndl_rpc1(data,_r)
        elif isinstance(data, list):
            rets = []
            for batched_rpc in data:
                _r = self.rsp2.copy()
                self._hndl_rpc1(batched_rpc,_r)
                rets.append(_r)
            return json.dumps(rets) if self.ret_str else rets
        return json.dumps(_r) if self.ret_str else _r
    
    async def handle_rpca(self, request):
        _r = self.rsp2.copy()
        data = self._hndl_parsing(request, _r)
        if isinstance(data, dict):
            await self._hndl_rpc1a(data,_r)
        elif isinstance(data, list):
            rets = []
            for batched_rpc in data:
                _r = self.rsp2.copy()
                await self._hndl_rpc1a(batched_rpc,_r)
                rets.append(_r)
                await asyncio.sleep(0)
            return json.dumps(rets) if self.ret_str else rets
        return json.dumps(_r) if self.ret_str else _r

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
