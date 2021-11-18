from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Protocol
from typing import Type
from typing import Union

from enum import Enum
from contextlib import contextmanager

from slxjsonrpc.schema.jsonrpc import RpcBatch
from slxjsonrpc.schema.jsonrpc import RpcError
from slxjsonrpc.schema.jsonrpc import RpcNotification
from slxjsonrpc.schema.jsonrpc import RpcRequest
from slxjsonrpc.schema.jsonrpc import RpcResponse

from slxjsonrpc.schema.jsonrpc import ErrorModel


JsonSchemas: Union[
    RpcError,
    RpcNotification,
    RpcRequest,
    RpcResponse
]


class RpcErrorException(Protocol):
    def __init__(self, code: int, msg: str, data=None) -> None: ...
    def get_rpc_model(self, id) -> RpcError: ...


class SlxJsonRpc(Protocol):

    def __init__(
            self,
            methods: Optional[Enum] = None,
            method_cb: Optional[Dict[Union[Enum, str], Callable[[Any], Any]]] = None,
            result: Optional[Dict[Union[Enum, str], Union[type, Type[Any]]]] = None,
            params: Optional[Dict[Union[Enum, str], Union[type, Type[Any]]]] = None,
        ): ...

    def create_request(
        self,
        method: Union[Enum, str],
        callback: Callable[[Any], None],
        error_callback: Optional[Callable[[ErrorModel], None]] = None,
        params: Optional[Any] = None,
    ) -> Optional[RpcRequest]: ...

    def create_notification(
        self,
        method: Union[Enum, str],
        params: Optional[Any] = None,
    ) -> Optional[RpcNotification]: ...

    @contextmanager
    def batch(self): ...

    def bulk_size(self) -> int: ...

    def get_batch_data(self) -> Optional[RpcBatch]: ...

    def parser(
        self,
        data: Union[bytes, str, dict]
    ) -> Union[RpcError, RpcResponse, None]: ...
