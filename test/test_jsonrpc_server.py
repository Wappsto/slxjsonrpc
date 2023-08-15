"""The pyTest Classes for testing the SlxJsonRpc Package."""
from enum import Enum

from typing import Any
from typing import List
# from typing import Literal  # NOTE: Not possible in py37
from typing import Union

import pytest

import slxjsonrpc


class MethodsTest(str, Enum):
    """The Enum of Methods for the SlXJsonRpc."""

    add = "add"
    ping = "ping"
    sub = "sub"
    crash = "crash"
    tweet = "tweet"
    error = "error"
    nop = 'NOP!'


class TestSlxJsonRpc:
    """Test the communication between the SlxJsonRpc Server & Client."""

    def setup_method(self):
        """Create the server & client instances for SlxJsonRpc."""
        self.tweet_data = None
        self.error_code = 0

        def tweeting(data):
            self.tweet_data = data

        def custom_error(*args, **kwargs):
            raise slxjsonrpc.RpcErrorException(
                code=self.error_code, msg="Just some Error!"
            )

        params = {
            MethodsTest.add: List[Union[int, float]],
            MethodsTest.sub: List[Union[int, float]],
            MethodsTest.ping: None,
            MethodsTest.crash: None,
            MethodsTest.tweet: Any,
            MethodsTest.error: Any,
            MethodsTest.nop: Any,
        }
        result = {
            MethodsTest.add: Union[int, float],
            MethodsTest.sub: Union[int, float],
            MethodsTest.ping: str,  # Literal["pong"]
            MethodsTest.crash: int,
            MethodsTest.tweet: None,
            MethodsTest.error: None,
            MethodsTest.nop: Any,
        }
        method_map = {
            MethodsTest.add: lambda data: sum(data),
            MethodsTest.sub: lambda data: data[0] - sum(data[1:]),
            MethodsTest.ping: lambda data: "pong",
            MethodsTest.crash: lambda *args: "*beep*" - 42,
            MethodsTest.tweet: lambda data: tweeting(data),
            MethodsTest.error: custom_error,
        }
        self.server = slxjsonrpc.SlxJsonRpc(
            methods=MethodsTest, result=result, params=params, method_cb=method_map
        )

    @pytest.mark.parametrize(
        "exclude_unset",
        [
            True,
            False,
        ],
    )
    @pytest.mark.parametrize(
        "exclude_none", [
            True,
            False,
        ],
    )
    @pytest.mark.parametrize(
        "exclude_defaults", [
            True,
            False,
        ],
    )
    @pytest.mark.parametrize(
        "data_in,data_out",
        [
            [
                '{"jsonrpc":"2.0","method":"add","id":"s1","params": [1, 2, 3]}',
                '{"jsonrpc":"2.0","id":"s1","result":6}',
            ],
            [
                '{"jsonrpc":"2.0","method":"ping","id":"s1122"}',
                '{"jsonrpc":"2.0","id":"s1122","result":"pong"}',
            ],
            [
                '{"jsonrpc":"2.0","method":"ping"}',
                None,
            ],
            [
                '{"jsonrpc":"2.0","method":"tweet","params":"test"}',
                None,
            ],
            # # NOTE:Will fail until pydantic v2 have an option to force result.
            # [
            #     '{"jsonrpc":"2.0","method":"tweet","id":"hh","params":"test"}',
            #     '{"jsonrpc":"2.0","id":"hh","result":null}',
            # ],
        ],
    )
    def test_flow(
        self,
        data_in: str,
        data_out: str,
        exclude_unset: bool,
        exclude_none: bool,
        exclude_defaults: bool,
    ):
        """Testing the server Happy Flow."""
        model_data = self.server.parser(data_in)

        if data_out is None:
            assert model_data is None
            return
        str_data = model_data.model_dump_json(
            exclude_unset=exclude_unset,
            exclude_none=exclude_none,
            exclude_defaults=exclude_defaults,
        )
        assert str_data == data_out

    @pytest.mark.parametrize(
        "exclude_unset",
        [
            True,
            False,
        ],
    )
    @pytest.mark.parametrize(
        "exclude_none", [
            True,
            False,
        ],
    )
    @pytest.mark.parametrize(
        "exclude_defaults", [
            True,
            False
        ]
    )
    @pytest.mark.parametrize(
        "data_in,data_out",
        [
            [
                '{"jsonrpc": "2.0", "method"',
                (
                    '{"jsonrpc":"2.0","error":'
                    '{"code":-32700,'
                    '"message":"Invalid JSON was received by the server.",'
                    '"data":"Expecting \':\' delimiter"}}'
                ),
            ],
            [
                "",
                (
                    '{"jsonrpc":"2.0","error":'
                    '{"code":-32700,'
                    '"message":"Invalid JSON was received by the server.",'
                    '"data":"Expecting value"}}'
                ),
            ],
            # # NOTE: Will fail until pydantic allow to force Exclude None.
            # [
            #     "[]",
            #     (
            #         '{"jsonrpc":"2.0","error":'
            #         '{"code":-32600,'
            #         '"message":"The JSON sent is not a valid Request object."}}'
            #     ),
            # ],
            [
                '{"foo":"boo"}',
                (
                    '{"jsonrpc":"2.0","error":'
                    '{"code":-32600,'
                    '"message":"The JSON sent is not a valid Request object.",'
                    '"data":{'
                    '"type":"missing","loc":["RpcNotification","method"],'
                    '"msg":"Field required","input":{"foo":"boo"},'
                    '"url":"https://errors.pydantic.dev/2.1/v/missing"}'
                    "}"
                    "}"
                ),
            ],
            [
                '{"jsonrpc":"2.0","method":"NOP!","params":"test", "id":"hej"}',
                (
                    '{"id":"hej","jsonrpc":"2.0",'
                    '"error":{"code":-32601,"message":"'
                    'The method does not exist '
                    '/ is not available.",'
                    '"data":"No Callback exists for given method: NOP!."}}'
                ),
            ],
            [
                '{"jsonrpc":"2.0","method":"NOP!","params":"test"}',
                (
                    '{"jsonrpc":"2.0",'
                    '"error":{"code":-32601,"message":"'
                    'The method does not exist '
                    '/ is not available.",'
                    '"data":"No Callback exists for given method: NOP!."}}'
                ),
            ],
            [
                '{"jsonrpc":"2.0","method":"NOWHERE!","id":"1q"}',
                (
                    '{"id":"1q","jsonrpc":"2.0","error":'
                    '{"code":-32601,'
                    '"message":"The method does not exist / is not available.",'
                    '"data":"Unknown method: NOWHERE!."}}'
                ),
            ],
            [
                '{"jsonrpc":"2.0","method":"NOWHERE!"}',
                (
                    '{"jsonrpc":"2.0","error":'
                    '{"code":-32601,'
                    '"message":"The method does not exist / is not available.",'
                    '"data":"Unknown method: NOWHERE!."}}'
                ),
            ],
            [
                '{"jsonrpc":"2.0","method":"add","id":"-32s1","params":"NOP!"}',
                (
                    '{"id":"-32s1","jsonrpc":"2.0","error":'
                    '{"code":-32602,'
                    '"message":"Invalid method parameter(s).",'
                    '"data":{"type":"list_type",'
                    '"loc":["RpcRequest","params"],'
                    '"msg":"Input should be a valid list",'
                    '"input":"NOP!",'
                    '"url":"https://errors.pydantic.dev/2.1/v/list_type"}}}'
                ),
            ],
            [
                '{"jsonrpc":"2.0","method":"add","params":"NOP!"}',
                (
                    '{"jsonrpc":"2.0","error":'
                    '{"code":-32602,'
                    '"message":"Invalid method parameter(s).",'
                    '"data":{"type":"list_type",'
                    '"loc":["RpcNotification","params"],'
                    '"msg":"Input should be a valid list",'
                    '"input":"NOP!",'
                    '"url":"https://errors.pydantic.dev/2.1/v/list_type"}}}'
                ),
            ],
            [
                '{"jsonrpc":"2.0","method":"add","id":"s102"}',
                (
                    '{"id":"s102","jsonrpc":"2.0","error":'
                    '{"code":-32602,'
                    '"message":"Invalid method parameter(s).",'
                    '"data":{"type":"list_type",'
                    '"loc":["RpcRequest","params"],'
                    '"msg":"Input should be a valid list",'
                    '"input":null,"url":"https://errors.pydantic.dev/2.1/v/list_type"}}}'
                ),
            ],
            [
                '{"jsonrpc":"2.0","method":"add"}',
                (
                    '{"jsonrpc":"2.0","error":'
                    '{"code":-32602,'
                    '"message":"Invalid method parameter(s).",'
                    '"data":{"type":"list_type","loc":["RpcNotification",'
                    '"params"],"msg":"Input should be a valid list",'
                    '"input":null,"'
                    'url":"https://errors.pydantic.dev/2.1/v/list_type"}}}'
                ),
            ],
            [
                '{"jsonrpc":"2.0","method":"crash","id":"12342"}',
                (
                    '{"id":"12342","jsonrpc":"2.0","error":'
                    '{"code":-32000,'
                    '"message":"Internal server error.",'
                    '"data":"unsupported operand type(s) for -:'
                    ' \'str\' and \'int\'"}}'
                ),
            ],
            [
                '{"jsonrpc":"2.0","method":"crash"}',
                (
                    '{"jsonrpc":"2.0","error":'
                    '{"code":-32000,'
                    '"message":"Internal server error.",'
                    '"data":"unsupported operand type(s) for -:'
                    ' \'str\' and \'int\'"}}'
                ),
            ],
            # # [-32099, ''],
        ],
    )
    def test_request_with_errors(
        self,
        data_in: str,
        data_out: str,
        exclude_unset: bool,
        exclude_none: bool,
        exclude_defaults: bool,
    ):
        """Testing the Request Happy Flow."""
        model_data = self.server.parser(data_in)

        if data_out is None:
            assert model_data is None
            return
        str_data = model_data.model_dump_json(
            exclude_unset=exclude_unset,
            exclude_none=exclude_none,
            exclude_defaults=exclude_defaults,
        )
        assert str_data == data_out

    @pytest.mark.parametrize(
        "data_in,data_out",
        [
            [
                '{"id":"12342","jsonrpc":"2.0","error":{"code":-32000,"message":"Internal server error."}}',
                None,
            ],
            [
                '{"jsonrpc":"2.0","error":{"code":-32000,"message":"Internal server error."}}',
                None,
            ],
        ],
    )
    def test_receive_of_error(
        self,
        data_in: str,
        data_out: str,
    ):
        """Testing if it do some unexpected when receiving an RpcError."""
        model_data = self.server.parser(data_in)

        assert model_data is None

    @pytest.mark.parametrize(
        "exclude_unset",
        [
            True,
            False,
        ],
    )
    @pytest.mark.parametrize(
        "exclude_none",
        [
            True,
            False,
        ],
    )
    @pytest.mark.parametrize(
        "exclude_defaults",
        [
            True,
            False,
        ],
    )
    @pytest.mark.parametrize(
        "data_in,data_out",
        [
            [
                (
                    '[{"jsonrpc":"2.0","method":"add","id":"s1","params":[1,2,3]},'
                    '{"jsonrpc":"2.0","method":"ping","id":"s1122"}]'
                ),
                (
                    '[{"jsonrpc":"2.0","id":"s1","result":6},'
                    '{"jsonrpc":"2.0","id":"s1122","result":"pong"}]'
                ),
            ],
            [
                '[{"jsonrpc":"2.0","method":"add","id":"s1","params":[1,2,3]}]',
                '[{"jsonrpc":"2.0","id":"s1","result":6}]',
            ],
            [
                '[{"jsonrpc":"2.0","method":"add","params":[1,2,3]}]',
                None,
            ],
            [
                (
                    '[{"foo":"boo"},'
                    '{"jsonrpc":"2.0","method":"add","id":"s1","params":[1,2,3]}]'
                ),
                (
                    '[{"jsonrpc":"2.0","error":'
                    '{"code":-32600,'
                    '"message":"The JSON sent is not a valid Request object.",'
                    '"data":{'
                    '"type":"missing","loc":["RpcNotification","method"],'
                    '"msg":"Field required","input":{"foo":"boo"},'
                    '"url":"https://errors.pydantic.dev/2.1/v/missing"}'
                    "}"
                    "},"
                    '{"jsonrpc":"2.0","id":"s1","result":6}]'
                ),
            ],
        ],
    )
    def test_received_bulk(
        self,
        data_in: str,
        data_out: str,
        exclude_unset: bool,
        exclude_none: bool,
        exclude_defaults: bool,
    ):
        """Test if the Bulking receiving works as intended."""
        model_data = self.server.parser(data_in)

        if data_out is None:
            assert model_data is None
            return
        str_data = model_data.model_dump_json(
            exclude_unset=exclude_unset,
            exclude_none=exclude_none,
            exclude_defaults=exclude_defaults,
        )
        assert str_data == data_out

    @pytest.mark.skip("TBW: Make server only.")
    @pytest.mark.parametrize(
        "error_code",
        # list(range(-32099, -32000 + 1)),
        [-32099, -32050, -32000],
    )
    def test_custom_error_response(self, error_code):
        """Test if the custom error response works as intended."""
        self.error_code = error_code
        msg = '{"jsonrpc": "2.0", "method": "error", "id": "12342"}'
        error_obj = self.server.parser(msg)
        obj_code = (
            error_obj.error.code
            if isinstance(error_obj.error.code, int)
            else error_obj.error.code.value
        )
        assert obj_code == error_code

    @pytest.mark.parametrize(
        "data_in,data_out",
        [
            [
                '{"jsonrpc":"2.0","method":"add","id":"s1","params": [1, 2, 3]}',
                (
                    '{"id":"s1","jsonrpc":"2.0","error":'
                    '{"code":-32603,'
                    '"message":"Internal JSON-RPC error.",'
                    '"data":"\'NoneType\' object has no attribute \'keys\'"}}'
                ),
            ],
            [
                '{"jsonrpc":"2.0","method":"add","params": [1, 2, 3]}',
                (
                    '{"jsonrpc":"2.0","error":'
                    '{"code":-32603,'
                    '"message":"Internal JSON-RPC error.",'
                    '"data":"\'NoneType\' object has no attribute \'keys\'"}}'
                ),
            ],
        ],
    )
    def test_internal_error(
        self,
        data_in: str,
        data_out: str,
    ):
        """Testing the server Happy Flow."""
        backup = self.server._method_cb
        self.server._method_cb = None
        model_data = self.server.parser(data_in)

        str_data = model_data.model_dump_json(
            exclude_none=True,
        )
        assert str_data == data_out

        self.server._method_cb = backup

    # @pytest.mark.parametrize(
    #     "data_in",
    #     [
    #         '{"jsonrpc":"2.1","id":"f","method":"ping"}',
    #     ],
    # )
    # def test_unknown_response_Type(
    #     self,
    #     data_in,
    # ):
    #     """For triggering the 'Unhanded ValidationError' logic."""
    #     #NOTE: Not possible.
    #     c_data = self.server.parser(
    #         data=data_in
    #     )
    #     print(c_data)
    #     assert False
