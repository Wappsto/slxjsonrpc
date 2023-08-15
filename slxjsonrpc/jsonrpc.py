# -*- coding: utf-8 -*-
"""Standalone JsonRpc module."""
import json
import logging

from contextlib import contextmanager

from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterator
from typing import List
from typing import Optional
from typing import overload
from typing import Type
from typing import Union

from enum import Enum

from pydantic import TypeAdapter
from pydantic import ValidationError
from pydantic_core import ErrorDetails

from slxjsonrpc.schema.jsonrpc import RpcBatch
from slxjsonrpc.schema.jsonrpc import RpcError
from slxjsonrpc.schema.jsonrpc import RpcErrorWithId
from slxjsonrpc.schema.jsonrpc import RpcErrorWithoutId
from slxjsonrpc.schema.jsonrpc import RpcNotification
from slxjsonrpc.schema.jsonrpc import RpcRequest
from slxjsonrpc.schema.jsonrpc import RpcResponse
from slxjsonrpc.schema.jsonrpc import RpcSchemas

from slxjsonrpc.schema.jsonrpc import ErrorModel
from slxjsonrpc.schema.jsonrpc import MethodError
from slxjsonrpc.schema.jsonrpc import rpc_set_name
from slxjsonrpc.schema.jsonrpc import RpcErrorCode
from slxjsonrpc.schema.jsonrpc import RpcErrorMsg
from slxjsonrpc.schema.jsonrpc import RpcVersion
from slxjsonrpc.schema.jsonrpc import set_id_mapping
from slxjsonrpc.schema.jsonrpc import set_params_map
from slxjsonrpc.schema.jsonrpc import set_result_map


class RpcErrorException(Exception):
    """
    Exception to reply a custom JsonRpc Error Response.

    This custom Exception extends the Exception class and implements
    a Rpc Error Code & message, to be transformed into the RpcError response.

    Attributes:
        Initializing with a msg & code arguments.
    """
    def __init__(
        self,
        code: Union[int, RpcErrorCode],
        msg: str,
        data: Optional[Any] = None
    ) -> None:
        """
        Initialize the RpcErrorException with the Rpc Error Response info.

        Args:
            code: The Rpc Error code, within the range of -32000 to -32099
            msg: The Rpc Error message, that shortly describe the error for given code.
            data: (Optional) The Rpc Extended error message.
        """
        super().__init__()
        self.code: Union[int, RpcErrorCode] = code
        self.msg: str = msg
        self.data: Optional[Any] = data

    def get_rpc_model(self, id: Union[str, int, None]) -> RpcError:
        """
        Returns a RpcError Response, for this given exception.

        The returned RpcError Model are used to send back to server,
        as a JsonRpc Error package.

        Args:
            id: The JsonRpc Id, for which this exception occurred.

        Returns:
            RpcError response fitting for this exception.
        """
        if id is None:
            return RpcErrorWithoutId(
                jsonrpc=RpcVersion.v2_0,
                error=ErrorModel(
                    code=self.code,
                    message=self.msg,
                    data=self.data
                )
            )

        return RpcErrorWithId(
            jsonrpc=RpcVersion.v2_0,
            id=id,
            error=ErrorModel(
                code=self.code,
                message=self.msg,
                data=self.data
            )
        )


def method_callback_example(params: Optional[Any]) -> Optional[Any]:
    """
    Structure of the Method Callback function.

    The method callback are called when data is received.

    If an error happens, and custom error code
    are needed, to send back, raise the RpcErrorException
    in the callback.

    Args:
        params: The parsed data from the RpcRequest 'params'-key.

    Returns:
        The Result of the request,
        that will be send in the 'result'-key in the RpcResponse.

    Raises:
        any: Will result in a RpcError with code: -32603
        RpcErrorException: custom RpcError code, message & data.
    """
    ...


class SlxJsonRpc:
    """
    SlxJsonRpc is a JsonRpc helper class, that uses pydantic2.

    SlxJsonRpc keep track of the JsonRpc schema, and procedure for each method.
    It also ensures to route each message to where it is expected.

    SlxJsonRpc is build to fill both the JsonRpc server & client roll.
    To enable the JsonRpc-server, the method_cb need to be given.
    """

    def __init__(
        self,
        methods: Optional[Enum] = None,
        method_cb: Optional[Dict[Union[Enum, str], Callable[[Any], Any]]] = None,
        result: Optional[Dict[Union[Enum, str], Union[type, Type[Any]]]] = None,
        params: Optional[Dict[Union[Enum, str], Union[type, Type[Any]]]] = None,
    ):
        """
        Initialization of the JsonRpc.

        # noqa: D417

        Args:
            method: (Optional) A String-Enum, with all the acceptable methods.
                    If not given, will there not be make checks for any wrong methods.
            method_cb: The mapping for each given method to a function call. (Server only)
                       Example given in `method_callback_example`.
            result: (Optional) The method & 'result' mapping.
                    If not given, will there not be make checks for any wrong 'result'.
            params: (Optional) The Parser method & 'params' mapping.
                    If not given, will there not be make checks for any wrong 'params'.
        """
        self.log: logging.Logger = logging.getLogger(__name__)
        self.log.addHandler(logging.NullHandler())

        rpc_set_name(None)
        if methods:
            RpcRequest.update_method(methods)
            RpcNotification.update_method(methods)
        if params:
            set_params_map(params)
        if result:
            set_result_map(result)

        self.__batch_lock: int = 0
        self.__batched_list: List[RpcSchemas] = []

        self.__parse_rpc_obj_w_id: TypeAdapter = TypeAdapter(Union[  # type: ignore
            RpcRequest,
            RpcResponse,
            RpcErrorWithId,
        ])
        self.__parse_rpc_obj_w_out_id: TypeAdapter = TypeAdapter(Union[  # type: ignore
            RpcNotification,
            RpcErrorWithoutId,
        ])

        self._method_cb: Dict[Union[Enum, str], Callable[[Any], Any]] = method_cb if method_cb else {}

        self._id_cb: Dict[Union[str, int, None], Callable[[Any], None]] = {}
        self._id_error_cb: Dict[Union[str, int, None], Callable[[Any], None]] = {}
        self._id_method: Dict[Union[str, int, None], Union[Enum, str]] = {}

        set_id_mapping(self._id_method)

    def create_request(
        self,
        method: Union[Enum, str],
        callback: Callable[[Any], None],
        error_callback: Optional[Callable[[ErrorModel], None]] = None,
        params: Optional[Any] = None,
    ) -> Optional[RpcRequest]:
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
                      The Callback gets the Result data model (if set)
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
            jsonrpc=RpcVersion.v2_0,
            method=method,
            params=params
        )

        self._add_result_handling(
            method=method,
            _id=r_data.id,
            callback=callback,
            error_callback=error_callback
        )

        return self._batch_filter(r_data)

    def _add_result_handling(
        self,
        method: Union[Enum, str],
        _id: Union[str, int, None],
        callback: Callable[[Any], None],
        error_callback: Optional[Callable[[ErrorModel], None]] = None,
    ) -> None:
        """Added handling for when a result comes back."""
        self._id_cb[_id] = callback
        if error_callback:
            self._id_error_cb[_id] = error_callback
        self._id_method[_id] = method

    def create_notification(
        self,
        method: Union[Enum, str],
        params: Optional[Any] = None,
    ) -> Optional[RpcNotification]:
        """
        Create a JsonRpc Notification, with given method & params.

        The Created Notification, are guaranteed to fit the given schema.
        Please note that there will not be a response for the notification
        send to the server.

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
            jsonrpc=RpcVersion.v2_0,
            method=method,
            params=params
        )

        return self._batch_filter(r_data)

    # -------------------------------------------------------------------------
    #                          Batching Functions
    # -------------------------------------------------------------------------

    @contextmanager
    def batch(self) -> Iterator[None]:
        """Batch RPC's within the context manager, into one RPC-Batch-List."""
        self.__batch_lock += 1
        try:
            yield
        finally:
            self.__batch_lock -= 1

    def batch_size(self) -> int:
        """Retrieve the number of packages in the Bulk."""
        return len(self.__batched_list)

    def get_batch_data(
        self,
        data: Optional[Union[RpcRequest, RpcNotification, RpcError, RpcResponse]] = None
    ) -> Optional[Union[RpcBatch, RpcRequest, RpcNotification, RpcError, RpcResponse]]:
        """
        Retrieve the Bulked packages.

        The returned Package, will be a RpcBatch,
        unless it was empty, where it will return `None`, or
        it only contain one package, then that will be returned instead.

        Args:
            data: (Optional) If given the data are added to the end of the batched data.

        Returns:
            RpcBatch, if there was batch anything.
            None, if nothing was batch.
        """
        if len(self.__batched_list) < 1:
            return None
        if data:
            self.__batched_list.append(data)
        batched_data = self.__batched_list.copy()
        self.__batched_list.clear()
        # NOTE: No need to return a batch of one, if we can avoid it.
        if len(batched_data) == 1:
            return batched_data[0]
        batch_obj: RpcBatch = RpcBatch.model_validate(batched_data)
        return batch_obj

    @overload
    def _batch_filter(self, data: RpcError) -> Optional[RpcError]: ...  # noqa: E704

    @overload
    def _batch_filter(self, data: RpcNotification) -> Optional[RpcNotification]: ...  # noqa: E704

    @overload
    def _batch_filter(self, data: RpcResponse) -> Optional[RpcResponse]: ...  # noqa: E704

    @overload
    def _batch_filter(self, data: RpcRequest) -> Optional[RpcRequest]: ...  # noqa: E704

    def _batch_filter(
        self,
        data: RpcSchemas,
    ) -> Optional[RpcSchemas]:
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

        self.__batched_list.append(data)
        return None

    # -------------------------------------------------------------------------
    #                          Parsing Functions
    # -------------------------------------------------------------------------

    def parser(
        self,
        data: Union[bytes, str, Dict[str, Any], List[Dict[str, Any]]]
    ) -> Optional[Union[RpcError, RpcResponse, RpcBatch]]:
        """
        Parse raw JsonRpc data, & returns the Response or Error.

        For the Parsed data, there will be make a check for any method
        callbacks, if found, the callback(s) will be called for the given data,
        and the return value from the callback will be packed into, a jsonrpc
        response package, and returned here.

        Everything returned from this method, should be passed on to the
        receiver, if not `None`.

        Args:
            data: The Raw data to be parsed.

        Returns:
            The fitting JsonRpc reply to the given data.
            None, if no reply are needed.
        """
        try:
            j_data: Union[Dict[str, Any], List[Dict[str, Any]]]
            if isinstance(data, dict) or isinstance(data, list):
                j_data = data
            else:
                j_data = json.loads(data)

        except json.decoder.JSONDecodeError as err:
            return self._batch_filter(RpcErrorWithoutId(
                jsonrpc=RpcVersion.v2_0,
                error=ErrorModel(
                    code=RpcErrorCode.ParseError,
                    message=RpcErrorMsg.ParseError,
                    data=err.msg
                )
            ))

        if not j_data:
            return self._batch_filter(RpcErrorWithoutId(
                jsonrpc=RpcVersion.v2_0,
                error=ErrorModel(
                    code=RpcErrorCode.InvalidRequest,
                    message=RpcErrorMsg.InvalidRequest,
                )
            ))

        if isinstance(j_data, list):
            b_data: List[Union[RpcError, RpcResponse]] = []
            for f_data in j_data:
                try:
                    temp = self._parse_data(f_data)
                except RpcErrorException as err:
                    b_data.append(err.get_rpc_model(
                        id=f_data['id'] if 'id' in f_data else None,
                    ))
                    continue
                if temp:
                    r_data = self.__reply_logic(temp)
                    if r_data:
                        b_data.append(r_data)
                # UNSURE: Is it required to return a batch of 1, if it was received as batch of 1?

            return RpcBatch.model_validate(b_data) if b_data else None

        try:
            p_data = self._parse_data(j_data)
        except RpcErrorException as err:
            return self._batch_filter(err.get_rpc_model(
                id=j_data['id'] if 'id' in j_data else None,
            ))
        return self.__reply_logic(p_data)

    def __reply_logic(
        self,
        p_data: RpcSchemas
    ) -> Optional[Union[RpcResponse, RpcError]]:
        try:
            if isinstance(p_data, (RpcErrorWithId, RpcErrorWithoutId)):
                return self._error_reply_logic(data=p_data)

            elif isinstance(p_data, RpcNotification):
                return self._notification_reply_logic(data=p_data)

            elif isinstance(p_data, RpcRequest):
                return self._request_reply_logic(data=p_data)

            elif isinstance(p_data, RpcResponse):
                return self._response_reply_logic(data=p_data)

        except RpcErrorException as err:
            return self._batch_filter(err.get_rpc_model(
                id=getattr(p_data, 'id', None),
            ))

        except Exception as err:
            self.log.exception(f"Normal: {err}")
            print(f"Normal: {err}")  # TODO: Testing needed to trigger this!
            return self._batch_filter(RpcErrorWithId(
                jsonrpc=RpcVersion.v2_0,
                id=getattr(p_data, 'id', None),
                error=ErrorModel(
                    code=RpcErrorCode.InternalError,
                    message=RpcErrorMsg.InternalError,
                    data=err.args[0],  # UNSURE: Is this a security problem?
                ),
            ))

    def _error_reply_logic(self, data: RpcError) -> Optional[RpcError]:
        if not hasattr(data, 'id'):
            return None
        if data.id not in self._id_cb.keys():
            # NOTE: Triggers only if it was an error that we generated.
            # NOTE: Triggers if the server receives an error.
            self.log.warning(f"Received an RpcError: {data}")
            return None
        self._id_cb.pop(data.id)
        if data.id not in self._id_error_cb.keys():
            self.log.warning(f"Unhanded error: {data}")
        else:
            with self._except_handler():
                cb = self._id_error_cb.pop(data.id)
                self.log.debug(f"Exec Error CB: {cb}")
                cb(data.error)
        return None

    def _notification_reply_logic(self, data: RpcNotification) -> Optional[RpcError]:
        if data.method not in self._method_cb.keys():
            return self._batch_filter(RpcErrorWithoutId(
                jsonrpc=RpcVersion.v2_0,
                error=ErrorModel(
                    code=RpcErrorCode.MethodNotFound,
                    message=RpcErrorMsg.MethodNotFound,
                    data=f"No Callback exists for given method: {data.method}.",
                ),
            ))
        with self._except_handler():
            cb = self._method_cb[data.method]
            self.log.debug(f"Exec Notification CB: {cb}")
            cb(data.params)
        return None

    def _request_reply_logic(self, data: RpcRequest) -> Optional[Union[RpcResponse, RpcError]]:
        if data.method in self._method_cb.keys():
            with self._except_handler():
                cb = self._method_cb[data.method]
                self.log.debug(f"Request CB: {cb}")
                result = cb(data.params)
            return self._batch_filter(RpcResponse(
                jsonrpc=RpcVersion.v2_0,
                id=data.id,
                result=result,
            ))
        # NOTE: Only triggered if no Callback for a given 'Method'.
        return self._batch_filter(RpcErrorWithId(
            jsonrpc=RpcVersion.v2_0,
            id=data.id,
            error=ErrorModel(
                code=RpcErrorCode.MethodNotFound,
                message=RpcErrorMsg.MethodNotFound,
                data=f"No Callback exists for given method: {data.method}.",
            ),
        ))

    def _response_reply_logic(self, data: RpcResponse) -> Optional[RpcResponse]:
        if data.id not in self._id_cb.keys():
            self.log.warning(f"Received an unknown RpcResponse: {data}")
        else:
            self._id_error_cb.pop(data.id, None)
            with self._except_handler():
                cb = self._id_cb.pop(data.id)
                self.log.debug(f"Exec Response CB: {cb}")
                cb(data.result)
        return None

    @contextmanager
    def _except_handler(self) -> Iterator[None]:
        try:
            yield
        except RpcErrorException:
            raise
        except Exception as err:
            # NOTE: Only triggered from user given function, or if it was not a function
            self.log.exception("An error happened doing execution of a callback.")
            raise RpcErrorException(
                code=RpcErrorCode.ServerError,
                msg=RpcErrorMsg.ServerError,
                data=err.args[0]
            ).with_traceback(err.__traceback__)

    def __ValidationError2ErrorModel(
        self,
        errors: List[ErrorDetails]
    ) -> Optional[ErrorModel]:
        # TODO (MBK): Find a faster/better way to do this!
        params_error = list(filter(lambda x: x['loc'][1] == 'params', errors))
        type_error = list(filter(lambda x: x['type'] in ["missing", "extra_forbidden"], errors))
        if params_error:
            raise RpcErrorException(
                code=RpcErrorCode.InvalidParams,
                msg=RpcErrorMsg.InvalidParams,
                data=params_error[0]
            )
        elif type_error:
            raise RpcErrorException(
                code=RpcErrorCode.InvalidRequest,
                msg=RpcErrorMsg.InvalidRequest,
                data=type_error[0]
            )

        # NOTE: Do not think if is possible to trigger!
        return None

    def _parse_data(
        self,
        data: Dict[str, Any]
    ) -> RpcSchemas:
        __parser = self.__parse_rpc_obj_w_id if 'id' in data.keys() else self.__parse_rpc_obj_w_out_id
        try:
            p_data: RpcSchemas = __parser.validate_python(data)
        except MethodError as error:
            raise RpcErrorException(
                code=RpcErrorCode.MethodNotFound,
                msg=RpcErrorMsg.MethodNotFound,
                data=error.args[0]
            )
        except ValidationError as error:
            error_package = self.__ValidationError2ErrorModel(
                errors=error.errors()
            )

            # NOTE: Do not think if is possible to trigger!
            # TODO: Testing needed to trigger this!
            if not error_package:
                self.log.exception(f"Unhanded ValidationError: {data}")
                raise

        return p_data
