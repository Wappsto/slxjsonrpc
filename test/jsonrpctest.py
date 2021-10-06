"""The pyTest Classes for testing the SlxJsonRpc Package."""
from enum import Enum

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


class TestSlxJsonRpc:
    """Test the communication between the SlxJsonRpc Server & Client."""

    def setup_method(self):
        """Setup the server & client instances of SlxJsonRpc."""
        params = {
            MethodsTest.add: List[Union[int, float]],
            MethodsTest.sub: List[Union[int, float]],
            MethodsTest.ping: None,
            MethodsTest.crash: None
        }
        result = {
            MethodsTest.add: Union[int, float],
            MethodsTest.sub: Union[int, float],
            MethodsTest.ping: str,  # Literal["pong"]
            MethodsTest.crash: int
        }
        method_map = {
            MethodsTest.add: lambda data: sum(data),
            MethodsTest.sub: lambda data: data[0] - sum(data[1:]),
            MethodsTest.ping: lambda data: "pong",
            MethodsTest.crash: lambda *args: "*beep*" - 42,
        }
        self.server = SlxJsonRpc(
            methods=MethodsTest,
            result=result,
            params=params,
            method_map=method_map
        )
        self.client = SlxJsonRpc(
            methods=MethodsTest,
            result=result,
            params=params,
            method_map=method_map
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
        "error_codes,data",
        [
            [-32700, '{"jsonrpc": "2.0", "method"'],
            [-32700, ""],
            [-32600, "[]"],
            [-32600, '{"foo": "boo"}'],
            [-32601, '{"jsonrpc": "2.0", "method": "NOWHERE!", "id": "1q"}'],
            [-32602, '{"jsonrpc": "2.0", "method": "add", "id": "s1", "params": "NOP!"}'],
            [-32602, '{"jsonrpc": "2.0", "method": "add", "id": "s1"}'],
            [-32603, '{"jsonrpc": "2.0", "method": "crash", "id": "12342"}'],
        ]
    )
    def test_request_errors(self, data, error_codes):
        """Testing the Request Happy Flow."""
        s_data = self.server.parser(data)
        print(f"{s_data}")
        assert s_data.error.code.value == error_codes

    # def test_bulk(self, method, params, result):
    #     pass
