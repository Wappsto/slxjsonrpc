"""Contains the JsonRpc Schemas used for the SlxJsonRpc Package."""
import random
import string

from enum import Enum

from pydantic import BaseModel
from pydantic import Extra
from pydantic import Field
from pydantic import validator
from pydantic import parse_obj_as
from pydantic.fields import ModelField


from typing import Any
from typing import Dict
from typing import Optional
from typing import List
from typing import Union

try:
    # https://github.com/ilevkivskyi/typing_inspect/issues/65
    # NOTE: py36 not a thing, py39 - types.GenericAlias
    from typing import _GenericAlias as GenericAlias
except ImportError:
    GenericAlias = type(List[Any])


_session_count: int = 0
_session_id: str = "".join(
    random.choices(string.ascii_letters + string.digits, k=10)
)

_RpcName: Optional[str] = "JsonRpc"


def rpc_set_name(name: Optional[str]):
    """Set the JsonRpc id name."""
    global _RpcName
    _RpcName = name


def rpc_get_name() -> Optional[str]:
    """Retrieve the JsonRpc id name."""
    global _RpcName
    return _RpcName


def _id_gen():
    """Create an unique Rpc-id."""
    global _session_count
    global _session_id
    global _RpcName
    _session_count += 1
    return f"{_session_id}_{_RpcName}_{_session_count}"


class RpcVersion(str, Enum):
    """The supported JsonRpc versions."""
    v2_0 = "2.0"


class BaseRPC(BaseModel):
    """The Base class for the RpcRequest, RpcResponse & RpcError schemas."""
    jsonrpc: Optional[RpcVersion] = RpcVersion.v2_0
    id: Optional[Union[str, int]] = None

    class Config:
        """Enforce that there can not be added extra keys to the BaseModel."""
        extra = Extra.forbid


###############################################################################
#                             JsonRpc Request Object
###############################################################################

params_mapping: Dict[str, Union[type, GenericAlias]] = {}


def set_params_map(map: Dict[str, Union[type, GenericAlias]]) -> None:
    global params_mapping
    params_mapping = map


class RpcRequest(BaseRPC):
    """The Standard JsonRpc Request Schema."""
    method: str
    params: Optional[Any]

    @validator('id', pre=True, always=True)
    def id_autofill(cls, v):
        """Validate the id, and auto-fill it is not set."""
        if rpc_get_name() is ...:
            rpc_set_name(v)
            return _id_gen()
        return v or _id_gen()

    @classmethod
    def update_method(cls, new_type: Enum):
        """Update the Method schema, to fit the new one."""
        new_fields = ModelField.infer(
            name="method",
            value=...,
            annotation=new_type,
            class_validators=None,
            config=cls.__config__
        )
        cls.__fields__['method'] = new_fields
        cls.__annotations__['method'] = new_type

    @validator("params", pre=True, always=True)
    def method_params_mapper(cls, v, values, **kwargs):
        """Check & enforce the params schema, depended on the method value."""
        global params_mapping

        if not params_mapping.keys():
            return v

        if values.get('method') not in params_mapping.keys():
            raise ValueError(f"Not valid params fro method: {values.get('method')}.")

        model = params_mapping[values.get('method')]
        if model is not None:
            return parse_obj_as(model, v)
        if v:
            raise ValueError("params should not be set.")


class RpcNotification(BaseModel):
    """
    The Standard JsonRpc Notification Schema.

    Supposed to be a Request Object, just without the 'id'.
    """
    jsonrpc: RpcVersion
    method: str
    params: Optional[Any]

    class Config:
        """Enforce that there can not be added extra keys to the BaseModel."""
        extra = Extra.forbid

    @classmethod
    def update_method(cls, new_type: Enum):
        """Update the Method schema, to fit the new one."""
        new_fields = ModelField.infer(
            name="method",
            value=...,
            annotation=new_type,
            class_validators=None,
            config=cls.__config__
        )
        cls.__fields__['method'] = new_fields
        cls.__annotations__['method'] = new_type

    @validator("params", pre=True, always=True)
    def method_params_mapper(cls, v, values, **kwargs):
        """Check & enforce the params schema, depended on the method value."""
        global params_mapping

        if not params_mapping.keys():
            return v

        if values.get('method') not in params_mapping.keys():
            raise ValueError(f"Not valid params fro method: {values.get('method')}.")

        model = params_mapping[values.get('method')]
        if model is not None:
            return parse_obj_as(model, v)
        if v:
            raise ValueError("params should not be set.")


###############################################################################
#                          JsonRpc Response Object
###############################################################################

class RpcResponse(BaseModel):
    """The Standard JsonRpc Response Schema."""
    jsonrpc: Optional[RpcVersion] = RpcVersion.v2_0
    id: Union[str, int]
    result: Any

    class Config:
        """Enforce that there can not be added extra keys to the BaseModel."""
        extra = Extra.forbid

    @classmethod
    def update_result(cls, new_type: GenericAlias):
        """Update the Method schema, to fit the new schema."""
        new_fields = ModelField.infer(
            name="result",
            value=...,
            annotation=new_type,
            class_validators=None,
            config=cls.__config__
        )
        cls.__fields__['result'] = new_fields
        cls.__annotations__['result'] = new_type


###############################################################################
#                             JsonRpc Error Object
###############################################################################

class RpcErrorCode(Enum):
    """
    JsonRpc Standard Error Codes.

    Error Codes:    Error code:         Message Description:
    ---
        -32700      Parse error         Invalid JSON was received by the server.
                                        An error occurred on the server while parsing the JSON text.
        -32600      Invalid Request     The JSON sent is not a valid Request object.
        -32601      Method not found    The method does not exist / is not available.

        -32602      Invalid params      Invalid method parameter(s).
        -32603      Internal error      Internal JSON-RPC error.
        -32000      Server error        IconServiceEngine internal error.
          ...
        -32099      Server error        IconServiceEngine internal error.
    """
    ParseError = -32700
    InvalidRequest = -32600
    MethodNotFound = -32601
    InvalidParams = -32602
    InternalError = -32603
    ServerError = -32000


class ErrorModel(BaseModel):
    """The Default JsonRpc Error message."""
    code: RpcErrorCode
    message: str
    data: Optional[Any]

    class Config:
        """Enforce that there can not be added extra keys to the BaseModel."""
        extra = Extra.forbid


class RpcError(BaseRPC):
    """The default JsonRpc Error Reply Schema."""
    error: ErrorModel


###############################################################################
#                             JsonRpc Batch Object
###############################################################################

class RpcBatch(BaseModel):
    """The Default JsonRpc Batch Schema."""
    __root__: List[Union[
        RpcRequest,
        RpcNotification,
        RpcResponse,
        RpcError,
        # Any,  # UNSURE:
    ]] = Field(..., min_items=1)
