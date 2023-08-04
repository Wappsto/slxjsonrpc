from enum import Enum, IntEnum
from pydantic import BaseModel, ConfigDict, FieldValidationInfo as FieldValidationInfo, RootModel
from typing import Any, Dict, List, Optional, Type, Union

def rpc_set_name(name: Optional[str]) -> None: ...
def rpc_get_name() -> Optional[str]: ...

class MethodError(Exception): ...

class RpcVersion(str, Enum):
    v2_0: str

params_mapping: Dict[Union[Enum, str], Union[type, Type[Any]]]

def set_params_map(mapping: Dict[Union[Enum, str], Union[type, Type[Any]]]) -> None: ...

class RpcRequest(BaseModel):
    jsonrpc: Optional[RpcVersion]
    method: str
    id: Optional[Union[str, int]]
    params: Optional[Any]
    model_config: ConfigDict  #type: ignore
    def id_autofill(cls, v: Optional[Union[str, int]], info: FieldValidationInfo) -> Union[str, int]: ...
    @classmethod
    def update_method(cls, new_type: Enum) -> None: ...
    def method_params_mapper(cls, v: Optional[Any], info: FieldValidationInfo) -> Any: ...

class RpcNotification(BaseModel):
    jsonrpc: Optional[RpcVersion]
    method: str
    params: Optional[Any]
    model_config: ConfigDict  #type: ignore
    @classmethod
    def update_method(cls, new_type: Enum) -> Any: ...
    def method_params_mapper(cls, v: Optional[Any], info: FieldValidationInfo) -> Any: ...

result_mapping: Dict[Union[Enum, str], Union[type, Type[Any]]]
id_mapping: Dict[Union[str, int, None], Union[Enum, str]]

def set_id_mapping(mapping: Dict[Union[str, int, None], Union[Enum, str]]) -> None: ...
def set_result_map(mapping: Dict[Union[Enum, str], Union[type, Type[Any]]]) -> None: ...

class RpcResponse(BaseModel):
    jsonrpc: Optional[RpcVersion]
    id: Union[str, int]
    result: Any
    model_config: ConfigDict  #type: ignore
    def method_params_mapper(cls, v: Any, info: FieldValidationInfo) -> Any: ...

class RpcErrorCode(IntEnum):
    ParseError: int
    InvalidRequest: int
    MethodNotFound: int
    InvalidParams: int
    InternalError: int
    ServerError: int

class RpcErrorMsg(str, Enum):
    ParseError: str
    InvalidRequest: str
    MethodNotFound: str
    InvalidParams: str
    InternalError: str
    ServerError: str

class ErrorModel(BaseModel):
    code: Union[int, RpcErrorCode]
    message: str
    data: Optional[Any]
    model_config: ConfigDict  #type: ignore
    def method_code_parser(cls, v: Union[str, bytes, int, float], info: FieldValidationInfo) -> Union[int, RpcErrorCode]: ...

class RpcError(BaseModel):
    id: Union[str, int, None]
    jsonrpc: Optional[RpcVersion]
    error: ErrorModel

class RpcBatch(RootModel[List[Union[RpcRequest, RpcNotification, RpcResponse, RpcError]]]):
    root: List[Union[RpcRequest, RpcNotification, RpcResponse, RpcError]]
