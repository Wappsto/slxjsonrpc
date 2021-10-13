from enum import Enum

from pydantic import BaseModel
from pydantic import Extra
from pydantic import Field
from pydantic import validator

from typing import Any
from typing import Dict
from typing import Optional
from typing import List
from typing import Union

try:
    # https://github.com/ilevkivskyi/typing_inspect/issues/65
    # NOTE: py36 not a thing, py39 - types.GenericAlias
    from typing import _GenericAlias as GenericAlias  # type: ignore
except ImportError:
    GenericAlias = type(List[Any])


def rpc_set_name(name: Optional[str]) -> None: ...


def rpc_get_name() -> Optional[str]: ...


def _id_gen() -> str: ...


class RpcVersion(str, Enum):
    """The supported JsonRpc versions."""
    v2_0 = "2.0"


class BaseRPC(BaseModel):
    jsonrpc: Optional[RpcVersion] = RpcVersion.v2_0
    id: Optional[Union[str, int]] = None

    class Config:
        extra = Extra.forbid


###############################################################################
#                             JsonRpc Request Object
###############################################################################

params_mapping: Dict[Union[Enum, str], Union[type, GenericAlias]]


def set_params_map(mapping: Dict[Union[Enum, str], Union[type, GenericAlias]]) -> None: ...


class RpcRequest(BaseRPC):
    method: str
    params: Optional[Any]

    @validator('id', pre=True, always=True)
    def id_autofill(cls, v) -> str: ...

    @classmethod
    def update_method(cls, new_type: Enum) -> None: ...

    @validator("params", pre=True, always=True)
    def method_params_mapper(cls, v, values, **kwargs) -> Any: ...


class RpcNotification(BaseModel):
    jsonrpc: Optional[RpcVersion] = RpcVersion.v2_0
    method: str
    params: Optional[Any]

    class Config:
        extra = Extra.forbid

    @classmethod
    def update_method(cls, new_type: Enum) -> Any: ...

    @validator("params", pre=True, always=True)
    def method_params_mapper(cls, v, values, **kwargs) -> Any: ...


###############################################################################
#                          JsonRpc Response Object
###############################################################################

class RpcResponse(BaseModel):
    jsonrpc: Optional[RpcVersion] = RpcVersion.v2_0
    id: Union[str, int]
    result: Any

    class Config:
        extra = Extra.forbid

    @classmethod
    def update_result(cls, new_type: GenericAlias) -> None: ...


###############################################################################
#                             JsonRpc Error Object
###############################################################################

class RpcErrorCode(Enum):
    ParseError = -32700
    InvalidRequest = -32600
    MethodNotFound = -32601
    InvalidParams = -32602
    InternalError = -32603
    ServerError = -32000


class RpcErrorMsg(str, Enum):
    ParseError = "Invalid JSON was received by the server."
    InvalidRequest = "The JSON sent is not a valid Request object."
    MethodNotFound = "The method does not exist / is not available."
    InvalidParams = "Invalid method parameter(s)."
    InternalError = "Internal JSON-RPC error."
    ServerError = "Internal server error."


class ErrorModel(BaseModel):
    code: Union[RpcErrorCode, int] = Field(None, le=-32001, ge=-32099)
    message: str
    data: Optional[Any]

    class Config:
        extra = Extra.forbid


class RpcError(BaseRPC):
    error: ErrorModel


###############################################################################
#                             JsonRpc Batch Object
###############################################################################

class RpcBatch(BaseModel):
    __root__: List[Union[
        RpcRequest,
        RpcNotification,
        RpcResponse,
        RpcError,
    ]] = Field(..., min_items=1)
