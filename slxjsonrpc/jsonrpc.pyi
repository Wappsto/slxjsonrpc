from _typeshed import Incomplete
from enum import Enum
from slxjsonrpc.schema.jsonrpc import ErrorModel as ErrorModel, MethodError as MethodError, RpcBatch as RpcBatch, RpcError as RpcError, RpcErrorCode as RpcErrorCode, RpcErrorMsg as RpcErrorMsg, RpcNotification as RpcNotification, RpcRequest as RpcRequest, RpcResponse as RpcResponse, rpc_set_name as rpc_set_name, set_id_mapping as set_id_mapping, set_params_map as set_params_map, set_result_map as set_result_map
from typing import Any, Callable, ContextManager, Dict, List, Optional, Type, Union

RpcSchemas = Union[RpcError, RpcNotification, RpcRequest, RpcResponse]

class RpcErrorException(Exception):
    code: Incomplete
    msg: Incomplete
    data: Incomplete
    def __init__(self, code: Union[int, RpcErrorCode], msg: str, data: Optional[Any] = ...) -> None: ...
    def get_rpc_model(self, id: Union[str, int, None]) -> RpcError: ...

class SlxJsonRpc:
    log: Incomplete
    def __init__(self, methods: Optional[Enum] = ..., method_cb: Optional[Dict[Union[Enum, str], Callable[[Any], Any]]] = ..., result: Optional[Dict[Union[Enum, str], Union[type, Type[Any]]]] = ..., params: Optional[Dict[Union[Enum, str], Union[type, Type[Any]]]] = ...) -> None: ...
    def create_request(self, method: Union[Enum, str], callback: Callable[[Any], None], error_callback: Optional[Callable[[ErrorModel], None]] = ..., params: Optional[Any] = ...) -> Optional[RpcRequest]: ...
    def create_notification(self, method: Union[Enum, str], params: Optional[Any] = ...) -> Optional[RpcNotification]: ...
    def batch(self) -> ContextManager[None]: ...
    def batch_size(self) -> int: ...
    def get_batch_data(self, data: Optional[Union[RpcRequest, RpcNotification, RpcError, RpcResponse]] = ...) -> Optional[Union[RpcBatch, RpcRequest, RpcNotification, RpcError, RpcResponse]]: ...
    def parser(self, data: Union[bytes, str, Dict[str, Any], List[Dict[str, Any]]]) -> Optional[Union[RpcError, RpcResponse, RpcBatch]]: ...
