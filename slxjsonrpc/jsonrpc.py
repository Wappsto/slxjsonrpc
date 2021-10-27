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
    from typing import _GenericAlias as GenericAlias  # type: ignore
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

RpcSchemas = Union[
    RpcError,
    RpcNotification,
    RpcRequest,
    RpcResponse
]


class RpcErrorException(Exception):
    """
    Exception to reply a custom JsonRpc Error Response.

    This custom Exception extends the Exception class and implements
    a Rpc Error Code & message, to be transformed into the RpcError response.

    Attributes:
        Initializing with a msg & code arguments.
    """
    def __init__(self, code: int, msg: str, data=None) -> None:
        """
        Initialize the RpcErrorException with the Rpc Error Response info.

        Args:
            code: The Rpc Error code, within the range of -32000 to -32099
            msg: The Rpc Error message, that shortly describe the error for given code.
            data: The Rpc
        """
        super().__init__()
        self.code = code
        self.msg = msg
        self.data = data

    def get_rpc_model(self, id) -> RpcError:
        """
        Returns a RpcError Response, for this given exception.

        Args:
            id: The JsonRpc Id, for which this exception occurred.

        Returns:
            RpcError response fitting for this exception.
        """
        return RpcError(
            id=id,
            error=ErrorModel(
                code=self.code,
                message=self.msg,
                data=self.data
            )
        )


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
                                  If an error happens, and custom error code
                                  are needed, to send back, raise the RpcErrorException
                                  in the callback.
            result: (Optional) The method & 'result' mapping.
                    If not given, will there not be make checks for any wrong 'result'.
            params: (Optional) The Parser method & 'params' mapping.
                    If not given, will there not be make checks for any wrong 'params'.
        """
        self.log = logging.getLogger(__name__)
        self.log.addHandler(logging.NullHandler())

        rpc_set_name(...)
        if methods:
            RpcRequest.update_method(methods)
            RpcNotification.update_method(methods)
        if params:
            set_params_map(params)

        self.__batch_lock: int = 0
        self.__batched_list: List[RpcSchemas] = []

        self._method_cb: Dict[Union[Enum, str], Callable[[Any], Any]] = method_cb if method_cb else {}

        # Workaround   # type: ignore for the Dict-keys to be None.
        self._id_cb: Dict[Union[str, int, None], Callable[[Any], None]] = {}
        self._id_ecb: Dict[Union[str, int, None], Callable[[Any], None]] = {}
        self._id_method: Dict[Union[str, int, None], Union[Enum, str]] = {}

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
        return parse_obj_as(RpcBatch, data)

    def _batch_filter(
        self,
        data: Union[RpcRequest, RpcNotification, RpcError, RpcResponse],
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
    ) -> Optional[Union[RpcError, RpcResponse, List[Union[RpcError, RpcResponse]]]]:
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
            j_data: Union[dict, list] = data if isinstance(data, dict) else json.loads(data)
        except json.decoder.JSONDecodeError as err:
            return self._batch_filter(RpcError(
                id=None,
                error=ErrorModel(
                    code=RpcErrorCode.ParseError,
                    message=RpcErrorMsg.ParseError,
                    data=err.msg
                )
            ))

        if not j_data:
            return self._batch_filter(RpcError(
                id=None,
                error=ErrorModel(
                    code=RpcErrorCode.InvalidRequest,  # UNSURE: RpcErrorCode.ServerError
                    message=RpcErrorMsg.InvalidRequest,  # UNSURE: RpcErrorMsg.ServerError
                )
            ))

        if isinstance(j_data, list):
            # TODO (MBK): Handle RpcBatch list, parse each single one for itself & Batch them.
            b_data: List[Union[RpcError, RpcResponse]] = []
            for f_data in j_data:
                temp = self.__reply_logic(self._parse_data(f_data))
                if temp:
                    b_data.append(temp)

            return parse_obj_as(RpcBatch, b_data)

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
    ) -> Union[RpcError, RpcResponse, None]:
        try:
            if isinstance(p_data, RpcError):
                return self._error_reply_logic(data=p_data)

            elif isinstance(p_data, RpcNotification):
                return self._notification_reply_logic(data=p_data)

            elif isinstance(p_data, RpcRequest):
                return self._request_reply_logic(data=p_data)

            elif isinstance(p_data, RpcResponse):
                return self._response_reply_logic(data=p_data)

        except RpcErrorException as err:
            return self._batch_filter(err.get_rpc_model(
                id=p_data.id if hasattr(p_data, 'id') else None,
            ))

        except Exception as err:
            print(f"Normal: {err}")  # TODO: Testing needed to trigger this!
            return self._batch_filter(RpcError(
                id=p_data.id if hasattr(p_data, 'id') else None,
                error=ErrorModel(
                    code=RpcErrorCode.InternalError,  # UNSURE: RpcErrorCode.ServerError
                    message=RpcErrorMsg.InternalError,  # UNSURE: RpcErrorMsg.ServerError
                    data=err.args[0]
                )
            ))

        return None

    def _error_reply_logic(self, data):
        if data.id not in self._id_cb.keys():
            return data
        self._id_cb.pop(data.id)
        if data.id not in self._id_ecb.keys():
            self.log.warning(f"Unhanded error: {data}")
        else:
            with self._except_handler():
                self._id_ecb.pop(data.id)(data.error)

    def _notification_reply_logic(self, data):
        if data.method not in self._method_cb.keys():
            return self._batch_filter(RpcError(
                id=None,
                error=ErrorModel(
                    code=RpcErrorCode.MethodNotFound,
                    message=RpcErrorMsg.MethodNotFound,
                    data=data.method
                )
            ))
        with self._except_handler():
            self._method_cb[data.method](data.params)

    def _request_reply_logic(self, data):
        if data.method in self._method_cb.keys():
            with self._except_handler():
                result = self._method_cb[data.method](data.params)
            return self._batch_filter(RpcResponse(
                id=data.id,
                jsonrpc=RpcVersion.v2_0,
                result=result
            ))
        return self._batch_filter(RpcError(
            id=data.id,
            error=ErrorModel(
                code=RpcErrorCode.MethodNotFound,
                message=RpcErrorMsg.MethodNotFound,
                data=data.method
            )
        ))

    def _response_reply_logic(self, data):
        if data.id not in self._id_cb.keys():
            self.log.warning(f"Received an unknown RpcResponse: {data}")
        else:
            self._id_ecb.pop(data.id, None)
            with self._except_handler():
                self._id_cb.pop(data.id)(data.result)

    @contextmanager
    def _except_handler(self):
        try:
            yield
        except RpcErrorException:
            raise
        except Exception as err:
            raise RpcErrorException(
                code=RpcErrorCode.ServerError,  # UNSURE: RpcErrorCode.InternalError
                msg=RpcErrorMsg.ServerError,  # UNSURE: RpcErrorMsg.InternalError
                data=err.args[0]
            ).with_traceback(err.__traceback__)

    def __ValidationError2ErrorModel(
        self,
        errors: List[Dict[str, Union[List[str], str, Dict[str, List[str]]]]]
    ) -> Optional[ErrorModel]:
        # Find a faster way to do this!
        method_error = list(filter(lambda x: x.get('type') == "type_error.enum", errors))
        params_error = list(filter(lambda x: x.get('loc') == ('__root__', 'params', '__root__'), errors))
        type_error = list(filter(lambda x: x.get('type') in ["value_error.missing", "value_error.extra"], errors))
        if method_error:
            raise RpcErrorException(
                code=RpcErrorCode.MethodNotFound,
                msg=RpcErrorMsg.MethodNotFound,
                data=method_error[0]
            )
        elif params_error:
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

        return None

    def _parse_data(
        self,
        data: dict
    ) -> RpcSchemas:
        try:
            p_data: RpcSchemas = parse_obj_as(
                RpcSchemas,  # type: ignore
                data
            )
        except ValidationError as error:
            error_package = self.__ValidationError2ErrorModel(
                errors=error.errors()
            )

            if not error_package:
                # TODO: Testing needed to trigger this!
                self.log.exception(f"Unhanded ValidationError: {data}")
                raise

        return p_data
