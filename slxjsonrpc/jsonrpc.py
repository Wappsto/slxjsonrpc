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
from slxjsonrpc.schema.jsonrpc import RpcErrorMsg
from slxjsonrpc.schema.jsonrpc import rpc_set_name
from slxjsonrpc.schema.jsonrpc import RpcVersion
from slxjsonrpc.schema.jsonrpc import set_params_map

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
    To enable the JsonRpc-server, the method_cb need to be given.
    """

    def __init__(
        self,
        methods: Optional[Enum] = None,
        method_cb: Optional[Dict[Union[Enum, str], Callable[[Any], Any]]] = None,
        result: Optional[Dict[Union[Enum, str], Union[type, GenericAlias]]] = None,
        params: Optional[Dict[Union[Enum, str], Union[type, GenericAlias]]] = None,
    ):
        """
        Initialization of the JsonRpc.

        # noqa: D417

        Args:
            method: (Optional) A String-Enum, with all the acceptable methods.
                    If not given, will there not be make checks for any wrong methods.
            method_cb: The mapping for each given method to a function call. (Server only)
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

        rpc_set_name(...)
        RpcRequest.update_method(methods)
        set_params_map(params)

        self.__batch_lock: int = 0
        self.__batched_list: RpcBatch = []

        self._method_cb: Dict[Union[Enum, str], Callable[[Any], Any]] = method_cb if method_cb else {}

        self._id_cb: Dict[str, Callable[[Any], None]] = {}
        self._id_ecb: Dict[str, Callable[[Any], None]] = {}
        self._id_method: Dict[str, Union[Enum, str]] = {}

    def create_request(
        self,
        method: Union[Enum, str],
        callback: Callable[[Any], None],
        error_callback: Optional[Callable[[ErrorModel], None]] = None,
        params: Optional[Any] = None,
    ) -> RpcRequest:
        """
        Create a JsonRpc Request, with given method & params.

        The Created Request, are guaranteed to fit the given schema.
        When the Request are created, it will make sure that when the reply
        for the given request are received (through the parser-method),
        it will be passed on to the callback.

        Args:
            method: Should be a apart of the given Method Enum, given on init,
                    or if not given, a string.
            callback: The function to be called when data is received.
                      The Callback gets the Result datamodel (if set)
                      else a Dict/List back as argument.
            error_callback: (Optional) The function to be called, when an error
                            have happened.
                            The callback gets an ErrorModel object as parameter.
            params: (Optional) Should be fitting the a DataModel,
                    if given on init, else a valid Dictionary or List.

        Returns:
            RpcRequest, That should be send.

        Raises:
            ValidationError, if the given data do not fit the given Schema.
        """
        r_data = RpcRequest(
            method=method,
            params=params
        )

        self._id_cb[r_data.id] = callback
        if error_callback:
            self._id_ecb[r_data.id] = error_callback
        self._id_method[r_data.id] = method

        self.log.debug(f"Request Package Created:{r_data}")

        return self._batch_filter(r_data)

    def create_notification(
        self,
        method: Union[Enum, str],
        params: Optional[Any] = None,
    ) -> RpcNotification:
        """
        Create a JsonRpc Notification, with given method & params.

        The Created Notification, are guaranteed to fit the given schema.

        Args:
            method: Should be a apart of the given Method Enum, given on init,
                    or if not given, a string.
            params: (Optional) Should be fitting the a DataModel,
                    if given on init, else a valid Dictionary or List.

        Returns:
            The RPCNotification, to be send.

        Raises:
            ValidationError, if the given data do not fit the given Schema.
        """
        r_data = RpcNotification(
            method=method,
            params=params
        )
        self.log.debug(f"Request Package Created:{r_data}")
        return self._batch_filter(r_data)

    # -------------------------------------------------------------------------
    #                          Batching Functions
    # -------------------------------------------------------------------------

    @contextmanager
    def batch(self):
        """Batch all RPC's called within the scope, into one RPC-Batch-List."""
        self.__batch_lock += 1
        try:
            yield
        finally:
            self.__batch_lock -= 1

    def bulk_size(self) -> int:
        """Retrieve the number of packages in the Bulk."""
        return len(self.__batched_list)

    def get_batch_data(self) -> Optional[RpcBatch]:
        """
        Retrieve the Bulked packages.

        Returns:
            RpcBatch, if there was batch anything.
            None, if nothing was batch.
        """
        if len(self.__batched_list) < 1:
            return None
        data = self.__batched_list.copy()
        self.__batched_list.clear()
        return RpcBatch(data)
        # return parse_obj_as(data, RpcBatch)

    def _batch_filter(
        self,
        data: Union[RpcRequest, RpcNotification, RpcError, RpcResponse]
    ) -> Optional[Union[RpcRequest, RpcNotification, RpcError, RpcResponse]]:
        """
        Check if batch is enabled, and return the right reply.

        Args:
            data: RpcPackage to be returned if batch is not enabled.

        Returns:
            None, If Batch is enabled.
            data, if Batch is disabled.
        """
        if not self.__batch_lock:
            return data

        self.log.debug(f"Batching of package: {data}")
        self.__batched_list.append(data)
        return None

    # -------------------------------------------------------------------------
    #                          Parsing Functions
    # -------------------------------------------------------------------------

    def parser(
        self,
        data: Union[bytes, str, dict]
    ) -> Union[RpcError, RpcResponse, None]:
        """
        Parse raw JsonRpc data, & returns the Response or Error.

        For the Parsed data, there will be check for any subscriptions,
        if found, this callback will be called, and given the data.

        TODO: Handle a received RpcError.
        TODO: Add to batched_list, instead of return, when in batch scope.

        Args:
            data: The Raw data to be parsed.

        Returns:
            The fitting JsonRpc reply to the given data.
            None, if no reply are needed.
        """
        try:
            j_data = data if isinstance(data, dict) else json.loads(data)
        except json.decoder.JSONDecodeError as err:
            return self._batch_filter(RpcError(
                id=None,
                error=ErrorModel(
                    code=RpcErrorCode.ParseError,
                    message=RpcErrorMsg.ParseError,
                    data=err.msg
                )
            ))

        # TODO (MBK): Handle RpcBatch list, parse each single one for itself.
        p_data = self._parse_data(j_data)

        try:
            if isinstance(p_data, RpcError):
                if p_data.id not in self._id_cb.keys():
                    return p_data
                self._id_cb.pop(p_data.id)
                if p_data.id not in self._id_ecb.keys():
                    self.log.warning(f"Unhanded error: {p_data}")
                else:
                    self._id_ecb.pop(p_data.id)(p_data.error)

            elif isinstance(p_data, RpcNotification):
                if p_data.method in self._method_cb.keys():
                    self._method_cb[p_data.method](p_data.params)
                else:
                    return self._batch_filter(RpcError(
                        id=None,
                        error=ErrorModel(
                            code=RpcErrorCode.MethodNotFound,
                            message=RpcErrorMsg.MethodNotFound,
                            data=p_data.method
                        )
                    ))

            elif isinstance(p_data, RpcRequest):
                if p_data.method in self._method_cb.keys():
                    result = self._method_cb[p_data.method](p_data.params)
                    return self._batch_filter(RpcResponse(
                        id=p_data.id,
                        jsonrpc=RpcVersion.v2_0,
                        result=result
                    ))
                return self._batch_filter(RpcError(
                    id=p_data.id,
                    error=ErrorModel(
                        code=RpcErrorCode.MethodNotFound,
                        message=RpcErrorMsg.MethodNotFound,
                        data=p_data.method
                    )
                ))

            elif isinstance(p_data, RpcResponse):
                if p_data.id not in self._id_cb.keys():
                    self.log.warning(f"Received an unknown RpcResponse: {p_data}")
                else:
                    self._id_cb.pop(p_data.id)(p_data.result)
        except Exception as err:
            return self._batch_filter(RpcError(
                id=p_data.id,
                error=ErrorModel(
                    code=RpcErrorCode.InternalError,
                    message=RpcErrorMsg.InternalError,
                    data=err.args[0]
                )
            ))

        return None

    def __ValidationError2ErrorModel(
        self,
        errors: List[Dict[str, Union[List[str], str, Dict[str, List[str]]]]]
    ) -> ErrorModel:
        method_error = list(filter(lambda x: x.get('type') == "type_error.enum", errors))
        params_error = list(filter(lambda x: x.get('loc') == ('__root__', 'params', '__root__'), errors))
        type_error = list(filter(lambda x: x.get('type') in ["value_error.missing", "value_error.extra"], errors))
        if method_error:
            return ErrorModel(
                code=RpcErrorCode.MethodNotFound,
                message=RpcErrorMsg.MethodNotFound,
                data=method_error[0]
            )
        elif params_error:
            return ErrorModel(
                code=RpcErrorCode.InvalidParams,
                message=RpcErrorMsg.InvalidParams,
                data=params_error[0]
            )
        elif type_error:
            return ErrorModel(
                code=RpcErrorCode.InvalidRequest,
                message=RpcErrorMsg.InvalidRequest,
                data=type_error[0]
            )

    def _parse_data(
        self,
        data: dict
    ) -> Union[RpcNotification, RpcRequest, RpcError, RpcResponse]:
        try:
            p_data: JsonSchemas = parse_obj_as(
                JsonSchemas,  # type: ignore
                data
            )
        except ValidationError as error:
            error_package = self.__ValidationError2ErrorModel(
                errors=error.errors()
            )

            if not error_package:
                self.log.exception(f"Unhanded ValidationError: {data}")
                raise

            return RpcError(
                jsonrpc=RpcVersion.v2_0,
                error=error_package
            )

        return p_data