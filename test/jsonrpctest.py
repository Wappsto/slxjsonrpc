"""The pyTest Classes for testing the SlxJsonRpc Package."""
from enum import Enum

from typing import Any
from typing import List
# from typing import Literal  # NOTE: Not possible in py37
from typing import Union

import pytest

from slxjsonrpc import SlxJsonRpc


class MethodsTest(str, Enum):
    """The Enum of Methods for the SlXJsonRpc."""
    add = "add"
    ping = "ping"
    sub = "sub"
    crash = "crash"
    tweet = "tweet"


class TestSlxJsonRpc:
    """Test the communication between the SlxJsonRpc Server & Client."""

    def setup_method(self):
        """Setup the server & client instances of SlxJsonRpc."""
        self.tweet_data = None

        def tweeting(data):
            self.tweet_data = data

        params = {
            MethodsTest.add: List[Union[int, float]],
            MethodsTest.sub: List[Union[int, float]],
            MethodsTest.ping: None,
            MethodsTest.crash: None,
            MethodsTest.tweet: Any,
        }
        result = {
            MethodsTest.add: Union[int, float],
            MethodsTest.sub: Union[int, float],
            MethodsTest.ping: str,  # Literal["pong"]
            MethodsTest.crash: int,
            MethodsTest.tweet: None
        }
        method_map = {
            MethodsTest.add: lambda data: sum(data),
            MethodsTest.sub: lambda data: data[0] - sum(data[1:]),
            MethodsTest.ping: lambda data: "pong",
            MethodsTest.crash: lambda *args: "*beep*" - 42,
            MethodsTest.tweet: lambda data: tweeting(data),
        }
        self.server = SlxJsonRpc(
            methods=MethodsTest,
            result=result,
            params=params,
            method_cb=method_map
        )
        self.client = SlxJsonRpc(
            methods=MethodsTest,
            result=result,
            params=params,
            method_cb=method_map
        )

    @pytest.mark.parametrize(
        "method,params,result",
        [
            ["ping", None, "pong"],
            ["add", [1, 2, 3], 6],
            ["sub", [1, 2, 3], -4],
        ]
    )
    def test_request_happy_flow(self, method, params, result):
        """Testing the Request Happy Flow."""
        round_trip = None

        def set_data(temp):
            nonlocal round_trip
            round_trip = temp

        c_data = self.client.create_request(
            method=method,
            params=params,
            callback=set_data
        )

        s_data = self.server.parser(c_data.json(exclude_none=True))
        self.client.parser(s_data.json(exclude_none=True))

        assert round_trip == result

    @pytest.mark.parametrize(
        "method,params,result",
        [
            ["tweet", "Trumphy", "Trumphy"],
            ["tweet", 1, 1],
        ]
    )
    def test_notification_happy_flow(self, method, params, result):
        """Testing the Request Happy Flow."""
        c_data = self.client.create_notification(
            method=method,
            params=params
        )

        s_data = self.server.parser(c_data.json(exclude_none=True))

        assert s_data is None
        assert self.tweet_data == result

    @pytest.mark.parametrize(
        "error_code,data",
        [
            [-32700, '{"jsonrpc": "2.0", "method"'],
            [-32700, ""],
            [-32600, "[]"],
            [-32600, '{"foo": "boo"}'],
            [-32601, '{"jsonrpc": "2.0", "method": "NOWHERE!", "id": "1q"}'],
            [-32602, '{"jsonrpc": "2.0", "method": "add", "id": "s1", "params": "NOP!"}'],
            [-32602, '{"jsonrpc": "2.0", "method": "add", "id": "s1"}'],
            [-32000, '{"jsonrpc": "2.0", "method": "crash", "id": "12342"}'],
            # [-32099, ''],
        ]
    )
    def test_request_errors(self, data, error_code):
        """Testing the Request Happy Flow."""
        s_data = self.server.parser(data)
        print(f"{s_data}")
        assert s_data.error.code.value == error_code

    # @pytest.mark.parametrize(
    #     "error_code, transformer",
    #     [
    #         [-32600, lambda data: {n: v for (n, v) in data.items() if n != 'result'}],
    #         # [-32600, lambda data: {n: v for (n, v) in data.items() if n != 'id'}],
    #         [-32600, lambda data: {n: v for (n, v) in data.items() if n != 'jsonrpc'}],
    #         [-32700, lambda data: json.dumps(data)[:-10]],
    #         [-32700, lambda data: None],
    #         [-32700, lambda data: None],
    #         [-32700, lambda data: None],
    #         [-32700, lambda data: None],
    #     ]
    # )
    # def test_return_types(self, error_code, transformer):
    #     """Testing if the return type is the right one."""
    #     error_obj = None

    #     def set_data(temp):
    #         nonlocal error_obj
    #         error_obj = temp

    #     c_data = self.client.create_request()
    #     s_data = self.server.parser(c_data.json(exclude_none=True))
    #     e_data = transformer(s_data)
    #     r_data = self.client.parser(e_data)

    #     assert r_data is None

    #     assert error_obj.code.value == error_code

    @pytest.mark.parametrize(
        "method,params",
        [
            [MethodsTest.ping, None],
            [MethodsTest.add, [1, 2, 3]],
            [MethodsTest.sub, [1, 2, 3]],
        ]
    )
    @pytest.mark.parametrize(
        "error_code, transformer",
        [
            [-32700, lambda data: {"jsonrpc": "2.0", "id": data.id, "error":
                                   {"code": -32700, "message": "", "data": "k"}
                                   }],
            [-32600, lambda data: {"jsonrpc": "2.0", "id": data.id, "error":
                                   {"code": -32600, "message": "", "data": "k"}
                                   }],
            [-32601, lambda data: {"jsonrpc": "2.0", "id": data.id, "error":
                                   {"code": -32601, "message": "", "data": "k"}
                                   }],
            [-32602, lambda data: {"jsonrpc": "2.0", "id": data.id, "error":
                                   {"code": -32602, "message": "", "data": "k"}
                                   }],
            [-32603, lambda data: {"jsonrpc": "2.0", "id": data.id, "error":
                                   {"code": -32603, "message": "", "data": "k"}
                                   }],
            [-32000, lambda data: {"jsonrpc": "2.0", "id": data.id, "error":
                                   {"code": -32000, "message": "", "data": "k"}
                                   }],
        ]
    )
    def test_error_response(self, method, params, error_code, transformer):
        """Testing handling of the response, when receiving an RpcError."""
        error_obj = None
        data_obj = None

        def set_error(temp):
            nonlocal error_obj
            error_obj = temp

        def set_data(temp):
            nonlocal data_obj
            data_obj = temp

        c_data = self.client.create_request(
            method=method,
            params=params,
            callback=set_data,
            error_callback=set_error
        )
        s_data = self.server.parser(c_data.json(exclude_none=True))
        e_data = transformer(s_data)
        r_data = self.client.parser(e_data)

        print(f"{r_data}")

        assert r_data is None
        assert data_obj is None
        assert error_obj.code.value == error_code

    # def test_bulk(self, method, params, result):
    #     """Test is the Bulking works as intended."""
    #     pass

    #         [-32099, lambda data: {"jsonrpc": "2.0", "id": data.id, "error":
    #                                {"code": -32099, "message": "", "data": "k"}
    #                                }],
    # # def test_custom_error_response(self):
    # #     """Test if the custom error response works as intended."""
    # #     pass
