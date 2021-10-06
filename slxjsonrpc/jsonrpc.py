"""Standalone JsonRpc module."""
import json
import logging

from contextlib import contextmanager

from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Union
try:
    # https://github.com/ilevkivskyi/typing_inspect/issues/65
    # NOTE: py36 not a thing, py39 - types.GenericAlias
    from typing import _GenericAlias as GenericAlias
except ImportError:
    GenericAlias = type(List[Any])

from enum import Enum

from pydantic import parse_obj_as
from pydantic import ValidationError

from slxjsonrpc.schema.jsonrpc import RpcBatch
from slxjsonrpc.schema.jsonrpc import RpcError
from slxjsonrpc.schema.jsonrpc import RpcNotification
from slxjsonrpc.schema.jsonrpc import RpcRequest
from slxjsonrpc.schema.jsonrpc import RpcResponse

from slxjsonrpc.schema.jsonrpc import ErrorModel
from slxjsonrpc.schema.jsonrpc import RpcErrorCode
from slxjsonrpc.schema.jsonrpc import RpcSetName
from slxjsonrpc.schema.jsonrpc import RpcVersion

JsonSchemas = Union[
    RpcError,
    RpcNotification,
    RpcRequest,
    RpcResponse
]


class SlxJsonRpc:
    """
    SlxJsonRpc is a JsonRpc helper class, that uses pydantic.

    SlxJsonRpc keep track of the JsonRpc schema, and procedure for each method.
    It also ensures to route each message to where it is expected.

    SlxJsonRpc is build to be both that JsonRpc server & client.
    To enable the JsonRpc-server, the method_map need to be given.
    """

    def __init__(
        self,
        methods: Optional[Enum] = None,
        method_map: Optional[Dict[Union[Enum, str], Callable[[Any], Any]]] = None,
        result: Optional[Dict[Union[Enum, str], Union[type, GenericAlias]]] = None,
        params: Optional[Dict[Union[Enum, str], Union[type, GenericAlias]]] = None,
    ):
        """
        Initialization of the JsonRpc.

        # noqa: D417

        Args:
            method: (Optional) A String-Enum, with all the acceptable methods.
                    If not given, will there not be make checks for any wrong methods.
            method_map: The mapping for each given method to a function call.
                        callback: The function to be call when data is received.
                                  The Callback gets the params definded in as args,
                                  & should return the Result defined.
            result: (Optional) The method & 'result' mapping.
                    If not given, will there not be make checks for any wrong 'result'.
            params: (Optional) The Parser method & 'params' mapping.
                    If not given, will there not be make checks for any wrong 'params'.
        """
        self.log = logging.getLogger(__name__)
        self.log.addHandler(logging.NullHandler())

        RpcSetName(...)

        self.batch_lock: int = 0
        self.batched_list: RpcBatch = []

        self._method_cb: Dict[Union[Enum, str], Callable[[Any], Any]] = method_map if method_map else {}

        self._id_cb: Dict[str, Callable[[Any], None]] = {}
        self._id_method: Dict[str, Union[Enum, str]] = {}

    def create_request(
        self,
        method: Union[Enum, str],
        callback: Callable[[Any], None],
        params: Optional[Any] = None,
    ) -> RpcRequest:
        """
        Create a JsonRpc Request, with given method & params.

        The Created Request, are guaranteed to fit the given schema.
        When the Request are created, it will make sure that when the reply
        for the given request are received (through the parser-method),
        it will be passed on to the callback.

        Args:
            method: Should be a apart of the given Method Enum, given on init, or if not given, a string.
            callback: The function to be call when data is received.
                      If not given, the function will be blocking until the response is received.
                      The Callback gets the Result datamodel (if set) back as argument.
            params: (Optional) Should be a DataModel, if given on init, else a json valid data.

        Returns:
            The reply for given request, or if callback is given, the ID of the request.

        Raises:
            ValidationError, if the given data do not fit the given Schema.
        """
        r_data = RpcRequest(
            method=method,
            params=params
        )

        self._id_cb[r_data.id] = callback
        self._id_method[r_data.id] = method

        if not self.batch_lock:
            return r_data

        self.batched_list.append(r_data)
        return None

    def create_notification(
        self,
        method: Union[Enum, str],
        params: Optional[Any] = None,
    ) -> RpcNotification:
        """
        Create a JsonRpc Notification, with given method & params.

        The Created Notification, are guaranteed to fit the given schema.

        Args:
            method: Should be a apart of the given Method Enum, given on init, or if not given, a string.
            params: (Optional) Should be a DataModel, if given on init, else a json valid data.

        Returns:
            The RPCNotification, to be send.

        Raises:
            ValidationError, if the given data do not fit the given Schema.
        """
        r_data = RpcNotification(
            method=method,
            params=params
        )

        if not self.batch_lock:
            return r_data

        self.batched_list.append(r_data)
        return None

    @contextmanager
    def batch(self) -> RpcBatch:
        """
        Batch all RPC's called within the scope, into one RPC-Batch-List.

        Returns:
            A list with all the RPC packages.
        """
        # UNSURE(MBK): Should this be a lock, or a count to make it multiple
        #              use safe?
        self.batch_lock += 1
        try:
            yield
        finally:
            self.batch_lock -= 1
            # return RPCBatch(self.batched_list)
            return parse_obj_as(self.batched_list, RpcBatch)

    def parser(
        self,
        data: Union[bytes, str, dict]
    ) -> Union[RpcError, RpcResponse, None]:
        """
        Parse raw JsonRpc data, & returns the Response/Error.

        For the Parsed data, there will be check for any subscriptions,
        if found, this callback will be called, and given the data

        Args:
            data: The Raw data to be parsed.

        Returns:
            The fitting JsonRpc reply to the given data.
            or None, if no reply are needed.

        # Raises:
        #     ValueError, if the given data are not a valid json.
        """
        j_data = data if isinstance(data, dict) else json.loads(data)

        # TODO (MBK): Handle RpcBatch list, parse each single one for itself.
        p_data = self._parse_data(j_data)

        if isinstance(p_data, RpcError):
            return p_data

        elif isinstance(p_data, RpcNotification):
            if p_data.method in self._method_cb.keys():
                self._method_cb[p_data.method](p_data.params)
                return None
            return ErrorModel(
                code=RpcErrorCode.MethodNotFound,
                message="Method Not Found",
                data="p_data.method"
            )

        elif isinstance(p_data, RpcRequest):
            if p_data.method in self._method_cb.keys():
                result = self._method_cb[p_data.method](p_data.params)
                return RpcResponse(
                    id=p_data.id,
                    jsonrpc=RpcVersion.v2_0,
                    result=result
                )
            return ErrorModel(
                code=RpcErrorCode.MethodNotFound,
                message="Method Not Found",
                data="p_data.method"
            )

        elif isinstance(p_data, RpcResponse):
            if p_data.id not in self._id_cb.keys():
                return ErrorModel(
                    code=RpcErrorCode.MethodNotFound,
                    message="Method Not Found",
                    data="p_data.method"
                )
            self._id_cb[p_data.id](p_data.result)

        return None

    def __ValidationError2ErrorModel(
        self,
        errors: List[Dict[str, Union[List[str], str, Dict[str, List[str]]]]]
    ) -> Union[ErrorModel, None]:
        # TODO(MBK): Make a algorithmic to prioritize the Errors.

        # This order?
        # 1) Method Not Found (Everything right except Method.)
        # 2) Invalid Parameter(s) (If the Data or values are wrong?)
        # 3) Invalid Request (Missing/Extra Keys or not a JSON/RPC)

        # any( {'enum_values': ["2.0"]} in err.values() for err in errors)
        # 1)
        # filter(lambda x: {'enum_values':list(self.methods)} in x.values(), errors)[0]
        # filter(lambda x: {'enum_values': list(RpcVersion)} in x.values(), errors)[0]
        # 2)
        # If result type is: Dict[str, int]
        #  {'loc': ('__root__', 'result'), 'msg': 'value is not a valid dict', 'type': 'type_error.dict'}]
        # If result type is: int
        # {'loc': ('__root__', 'result'), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'}]

        # 3)
        # filter(lambda x: {'type': 'value_error.extra'} in x-values(), errors)[0]
        # filter(lambda x: {'type': 'value_error.missing'} in x-values(), errors)[0]
        #
        e_type = errors[0]
        if e_type['type'] in ["value_error.missing", "value_error.extra"]:
            return ErrorModel(
                code=RpcErrorCode.InvalidRequest,
                message="Invalid Request",
                data=e_type
            )
        elif e_type['type'] == "type_error.enum":

            if "method" in e_type["loc"]:
                return ErrorModel(
                    code=RpcErrorCode.MethodNotFound,
                    message="Method Not Found",
                    data=e_type
                )

            return ErrorModel(
                code=RpcErrorCode.InvalidParams,
                message="Invalid parameter(s)",
                data=e_type
            )

            # TODO(MBK): Handle when RPCSuccess->result is wrong, exception.
            #            If that happens... 'Invalid paramter'?

        return None

    def _parse_data(
        self,
        data: dict
    ) -> Union[RpcNotification, RpcRequest, RpcError, RpcResponse]:
        try:
            p_data: JsonSchemas = parse_obj_as(
                JsonSchemas,  # type: ignore
                data
            )
        except json.JSONDecodeError:
            return RpcError(
                id=None,
                jsonrpc=RpcVersion.v2_0,
                error=ErrorModel(
                    code=RpcErrorCode.ParseError,
                    message="Parse error",
                    data=data
                ),
            )
        except ValidationError as error:
            error_package = self.__ValidationError2ErrorModel(
                errors=error.errors()
            )

            if not error_package:
                self.log.exception("Unhanded ValidationError.")
                raise

            return RpcError(
                jsonrpc=RpcVersion.v2_0,
                error=error_package
            )

        return p_data
