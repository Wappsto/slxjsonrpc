"""
Contains the JsonRpc Schemas used for the SlxJsonRpc Package.

The slxJsonRpc are build with the specification in mind, listed here:
    https://www.jsonrpc.org/specification
"""
import random
import string

from enum import Enum
from enum import IntEnum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from pydantic import FieldValidationInfo
from pydantic import RootModel
from pydantic import TypeAdapter
from pydantic.fields import FieldInfo


from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Type
from typing import Union


_session_count: int = 0
_session_id: str = "".join(
    random.choices(string.ascii_letters + string.digits, k=10)
)

_RpcName: Optional[str] = None


def rpc_set_name(name: Optional[str]) -> None:
    """Set the JsonRpc id name."""
    global _RpcName
    _RpcName = name


def rpc_get_name() -> Optional[str]:
    """Retrieve the JsonRpc id name."""
    global _RpcName
    return _RpcName


def _id_gen(name: Optional[Union[str, int, float]] = None) -> str:
    """Create an unique Rpc-id."""
    global _session_count
    global _session_id
    global _RpcName
    rpc_name = name if name else _RpcName
    _session_count += 1
    return f"{_session_id}_{rpc_name}_{_session_count}"


class MethodError(Exception):
    """Exception to track if the Method is wrong."""
    pass


class RpcVersion(str, Enum):
    """The supported JsonRpc versions."""
    v2_0 = "2.0"


###############################################################################
#                             JsonRpc Request Object
###############################################################################

params_mapping: Dict[Union[Enum, str], Union[type, Type[Any]]] = {}


def set_params_map(mapping: Dict[Union[Enum, str], Union[type, Type[Any]]]) -> None:
    """Set the method to params schema mapping."""
    global params_mapping
    params_mapping = mapping


class RpcRequest(BaseModel):
    """
    The Standard JsonRpc Request Schema, used to do a request of the server.

    Attributes:
        jsonrpc: The JsonRpc version this schema is using. (Default v2.0)
        id: A identifier set by the client. (If emitted it will be auto generated)
        method: The name of the method to be invoked.
        params: (Optional) The input parameters for the invoked method.
    """
    jsonrpc: Optional[RpcVersion] = RpcVersion.v2_0
    method: Union[Enum, str]
    id: Union[str, int] = Field(default_factory=lambda: _id_gen(name=rpc_get_name()))
    params: Optional[Any] = Field(default=None, validate_default=True)

    """Enforce that there can not be added extra keys to the BaseModel."""
    model_config: ConfigDict = ConfigDict(extra='forbid')  # type: ignore

    @field_validator('id', mode='before')
    def id_autofill(cls, v: Optional[Union[str, int]], info: FieldValidationInfo) -> Union[str, int]:
        """Validate the id, and auto-fill it is not set."""
        return v or _id_gen(name=rpc_get_name() or info.data.get('method'))

    @classmethod
    def update_method(cls, new_type: Enum) -> None:
        """Update the Method schema, to fit the new one."""
        cls.model_fields['method'] = FieldInfo(
            annotation=new_type,
        )
        cls.__annotations__['method'] = new_type

    @field_validator("params")
    def method_params_mapper(cls, v: Optional[Any], info: FieldValidationInfo) -> Any:
        """Check & enforce the params schema, depended on the method value."""
        global params_mapping

        if not params_mapping.keys():
            return v

        if info.data.get('method') is None:
            # UNSURE: Why is this needed, when MethodError is use instead of ValueError? o.0
            return v

        if info.data.get('method') not in params_mapping.keys():
            raise MethodError(f"Unknown method: {info.data.get('method')}.")

        model = params_mapping[info.data['method']]

        if isinstance(model, BaseModel):
            return model.model_validate(v)

        if model is not None:
            model_converter: TypeAdapter = TypeAdapter(model)  # type: ignore
            return model_converter.validate_python(v)

        if v:
            raise ValueError("params should not be set.")


class RpcNotification(BaseModel):
    """
    The Standard JsonRpc Notification Schema, to Notifies the server of change.

    Supposed to be a Request Object, just without the 'id'.

    Attributes:
        jsonrpc: The JsonRpc version this schema is using. (Default v2.0)
        method: The name of the method to be invoked.
        params: (Optional) The input parameters for the invoked method.
    """
    jsonrpc: Optional[RpcVersion] = RpcVersion.v2_0
    method: Union[Enum, str]
    params: Optional[Any] = Field(default=None, validate_default=True)

    """Enforce that there can not be added extra keys to the BaseModel."""
    model_config: ConfigDict = ConfigDict(extra='forbid')  # type: ignore

    @classmethod
    def update_method(cls, new_type: Enum) -> Any:
        """Update the Method schema, to fit the new one."""
        cls.model_fields['method'] = FieldInfo(
            annotation=new_type,
        )
        cls.__annotations__['method'] = new_type

    @field_validator("params")
    def method_params_mapper(cls, v: Optional[Any], info: FieldValidationInfo) -> Any:
        """Check & enforce the params schema, depended on the method value."""
        global params_mapping

        if not params_mapping.keys():
            return v

        if info.data.get('method') is None:
            # UNSURE: Why is this needed, when MethodError is use instead of ValueError? o.0
            return v

        if info.data.get('method') not in params_mapping.keys():
            raise MethodError(f"Unknown method: {info.data.get('method')}.")

        model = params_mapping[info.data['method']]

        if isinstance(model, BaseModel):
            return model.model_validate(v)

        if model is not None:
            model_converter: TypeAdapter = TypeAdapter(model)  # type: ignore
            return model_converter.validate_python(v)

        if v:
            raise ValueError("params should not be set.")


###############################################################################
#                          JsonRpc Response Object
###############################################################################

result_mapping: Dict[Union[Enum, str], Union[type, Type[Any]]] = {}

id_mapping: Dict[Union[str, int, None], Union[Enum, str]] = {}


def set_id_mapping(mapping: Dict[Union[str, int, None], Union[Enum, str]]) -> None:
    """Set the id to method mapping."""
    global id_mapping
    id_mapping = mapping


def set_result_map(mapping: Dict[Union[Enum, str], Union[type, Type[Any]]]) -> None:
    """Set the method to params schema mapping."""
    global result_mapping
    result_mapping = mapping


class RpcResponse(BaseModel):
    """The Standard JsonRpc Response Schema, that is responded with.

    Attributes:
        jsonrpc: The JsonRpc version this schema is using. (Default v2.0)
        id: Must be the same value as the object this is a response to.
        result: The result of the Request object, if it did not fail.
    """
    jsonrpc: Optional[RpcVersion] = RpcVersion.v2_0
    id: Union[str, int]
    result: Any = Field(validate_default=True)

    """Enforce that there can not be added extra keys to the BaseModel."""
    model_config: ConfigDict = ConfigDict(extra='forbid')  # type: ignore

    @field_validator("result", mode='before')
    def method_params_mapper(cls, v: Any, info: FieldValidationInfo) -> Any:
        """Check & enforce the params schema, depended on the method value."""
        global result_mapping
        global method_id_mapping

        if not result_mapping.keys():
            return v

        the_id = info.data.get('id')

        if the_id not in id_mapping:
            # UNSURE (MBK): What should done, when it was not meant for this receiver?
            return v

        the_method = id_mapping[the_id]

        if the_method not in result_mapping.keys():
            raise ValueError(f"Not valid params for method: {info.data.get('method')}.")

        model = result_mapping[the_method]

        if isinstance(model, BaseModel):
            return model.model_validate(v)

        if model is not None:
            model_converter: TypeAdapter = TypeAdapter(model)  # type: ignore
            return model_converter.validate_python(v)

        if v:
            raise ValueError("result should not be set.")


###############################################################################
#                             JsonRpc Error Object
###############################################################################

class RpcErrorCode(IntEnum):
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
        -32000      Server error        Internal error.
          ...
        -32099      Server error        Internal error.
    """
    ParseError = -32700
    InvalidRequest = -32600
    MethodNotFound = -32601
    InvalidParams = -32602
    InternalError = -32603
    ServerError = -32000


class RpcErrorMsg(str, Enum):
    """
    JsonRpc Standard Error Messages.

    Error Codes:    Error code:         Message Description:
    ---
        -32700      Parse error         Invalid JSON was received by the server.
                                        An error occurred on the server while parsing the JSON text.
        -32600      Invalid Request     The JSON sent is not a valid Request object.
        -32601      Method not found    The method does not exist / is not available.

        -32602      Invalid params      Invalid method parameter(s).
        -32603      Internal error      Internal JSON-RPC error.
        -32000      Server error        Internal error.
          ...
        -32099      Server error        Internal error.
    """
    ParseError = "Invalid JSON was received by the server."
    InvalidRequest = "The JSON sent is not a valid Request object."
    MethodNotFound = "The method does not exist / is not available."
    InvalidParams = "Invalid method parameter(s)."
    InternalError = "Internal JSON-RPC error."
    ServerError = "Internal server error."


class ErrorModel(BaseModel):
    """
    The Default JsonRpc Error message, that is responded with on error.

    Attributes:
        code: The error code.
        message: A short describing of the error.
        data: (Optional), a Additional information of the error.
    """
    code: Union[int, RpcErrorCode]
    message: str
    data: Optional[Any] = None

    """Enforce that there can not be added extra keys to the BaseModel."""
    model_config: ConfigDict = ConfigDict(extra='forbid')  # type: ignore

    @field_validator("code")
    def method_code_parser(
        cls,
        v: Union[str, bytes, int, float],
        info: FieldValidationInfo
    ) -> Union[int, RpcErrorCode]:
        """Error code parser."""
        value = int(v)

        if -32100 < value < -32000:
            return value

        return RpcErrorCode(value)


class RpcError(BaseModel):
    """
    The default JsonRpc Error Reply Schema.

    Attributes:
        jsonrpc:
        id:
        error:
    """
    id: Union[str, int, None] = None
    jsonrpc: Optional[RpcVersion] = RpcVersion.v2_0
    error: ErrorModel


###############################################################################
#                             JsonRpc Batch Object
###############################################################################

class RpcBatch(RootModel[List[Union[RpcRequest, RpcNotification, RpcResponse, RpcError]]]):
    """The Default JsonRpc Batch Schema."""
    root: List[Union[
        RpcRequest,
        RpcNotification,
        RpcResponse,
        RpcError,
    ]] = Field(..., min_length=1)
