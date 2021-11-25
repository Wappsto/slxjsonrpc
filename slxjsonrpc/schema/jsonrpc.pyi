from enum import Enum

from pydantic import BaseModel
from pydantic import Extra
from pydantic import Field
from pydantic import validator

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Type
from typing import Union


def rpc_set_name(name: Optional[str]) -> None: ...


def rpc_get_name() -> Optional[str]: ...


def _id_gen(name: Optional[Union[str, int, float]] = None) -> str: ...


class RpcVersion(str, Enum):
    """The supported JsonRpc versions."""
    v2_0 = "2.0"


###############################################################################
#                             JsonRpc Request Object
###############################################################################

params_mapping: Dict[Union[Enum, str], Union[type, Type[Any]]]


def set_params_map(mapping: Dict[Union[Enum, str], Union[type, Type[Any]]]) -> None: ...


class RpcRequest(BaseModel):
    jsonrpc: Optional[RpcVersion] = RpcVersion.v2_0
    method: str
    id: Optional[Union[str, int]] = None
    params: Optional[Any]

    @validator('id', pre=True, always=True)
    def id_autofill(cls, v, values, **kwargs) -> str: ...

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

result_mapping: Dict[Union[Enum, str], Union[type, Type[Any]]] = {}
id_mapping: Dict[Union[str, int, None], Union[Enum, str]] = {}


def set_id_mapping(mapping: Dict[Union[str, int, None], Union[Enum, str]]) -> None: ...


def set_result_map(mapping: Dict[Union[Enum, str], Union[type, Type[Any]]]) -> None: ...


class RpcResponse(BaseModel):
    jsonrpc: Optional[RpcVersion] = RpcVersion.v2_0
    id: Union[str, int]
    result: Any

    class Config:
        extra = Extra.forbid

    @validator("result", pre=True, always=True)
    def method_params_mapper(cls, v, values, **kwargs) -> Any: ...


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


class RpcError(BaseModel):
    id: Union[str, int, None] = None
    jsonrpc: Optional[RpcVersion] = RpcVersion.v2_0
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
