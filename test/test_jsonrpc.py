"""The pyTest Classes for testing the SlxJsonRpc Package."""
from enum import Enum

from typing import Any
from typing import List

# from typing import Literal  # NOTE: Not possible in py37
from typing import Union

import pytest

import slxjsonrpc

from pydantic import BaseModel


class Point(BaseModel):
    """Coordinate Point Object."""
    x: int
    y: int


class MethodsTest(str, Enum):
    """The Enum of Methods for the SlXJsonRpc."""

    add = "add"
    ping = "ping"
    sub = "sub"
    crash = "crash"
    tweet = "tweet"
    error = "error"
    point = "point"


class TestSlxJsonRpc:
    """Test the communication between the SlxJsonRpc Server & Client."""

    def setup_method(self):
        """Setup the server & client instances of SlxJsonRpc."""
        self.tweet_data = None
        self.error_code = 0

        def tweeting(data):
            self.tweet_data = data

        def custom_error(*args, **kwargs):
            raise slxjsonrpc.RpcErrorException(
                code=self.error_code,
                msg="Just some Error!",
            )

        params = {
            MethodsTest.add: List[Union[int, float]],
            MethodsTest.sub: List[Union[int, float]],
            MethodsTest.ping: None,
            MethodsTest.crash: None,
            MethodsTest.tweet: Any,
            MethodsTest.error: Any,
            MethodsTest.point: Point,
        }
        result = {
            MethodsTest.add: Union[int, float],
            MethodsTest.sub: Union[int, float],
            MethodsTest.ping: str,  # Literal["pong"]
            MethodsTest.crash: int,
            MethodsTest.tweet: None,
            MethodsTest.error: None,
            MethodsTest.point: Point,
        }
        method_map = {
            MethodsTest.add: lambda data: sum(data),
            MethodsTest.sub: lambda data: data[0] - sum(data[1:]),
            MethodsTest.ping: lambda data: "pong",
            MethodsTest.crash: lambda *args: "*beep*" - 42,
            MethodsTest.tweet: lambda data: tweeting(data),
            MethodsTest.error: custom_error,
            MethodsTest.point: lambda data: Point(x=data.x * 2, y=data.y * 2),
        }
        self.server = slxjsonrpc.SlxJsonRpc(
            methods=MethodsTest,
            result=result,
            params=params,
            method_cb=method_map
        )
        self.client = slxjsonrpc.SlxJsonRpc(
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
            ['point', Point(x=1, y=2), Point(x=2, y=4)],
        ],
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

        s_data = self.server.parser(c_data.model_dump_json(exclude_none=True))
        self.client.parser(s_data.model_dump_json(exclude_none=True))

        assert round_trip == result

    @pytest.mark.parametrize(
        "method,params,result",
        [
            ["tweet", "Trumphy", "Trumphy"],
            ["tweet", 1, 1],
            ['point', Point(x=1, y=2), None],
        ],
    )
    def test_notification_happy_flow(self, method, params, result):
        """Testing the Request Happy Flow."""
        c_data = self.client.create_notification(
            method=method,
            params=params
        )

        s_data = self.server.parser(c_data.model_dump_json(exclude_none=True))

        assert s_data is None
        if result:
            assert self.tweet_data == result

    @pytest.mark.parametrize(
        "error_code,data",
        [
            [-32700, '{"jsonrpc": "2.0", "method"'],
            [-32700, ""],
            [-32600, "[]"],
            [-32600, '{"foo": "boo"}'],
            [-32601, '{"jsonrpc": "2.0", "method": "NOWHERE!", "id": "1q"}'],
            [-32601, '{"jsonrpc": "2.0", "method": "NOWHERE!"}'],
            [-32602, '{"jsonrpc": "2.0", "method": "add", "id": "s1", "params": "NOP!"}'],
            [-32602, '{"jsonrpc": "2.0", "method": "add", "params": "NOP!"}'],
            [-32602, '{"jsonrpc": "2.0", "method": "add", "id": "s1"}'],
            [-32602, '{"jsonrpc": "2.0", "method": "add"}'],
            [-32000, '{"jsonrpc": "2.0", "method": "crash", "id": "12342"}'],
            [-32000, '{"jsonrpc": "2.0", "method": "crash"}'],
            # [-32099, ''],
        ],
    )
    def test_request_errors(self, data, error_code):
        """Testing the Request Happy Flow."""
        s_data = self.server.parser(data)
        print(f"{s_data}")
        assert s_data.error.code.value == error_code

    @pytest.mark.skip(reason="TBW!")
    @pytest.mark.parametrize("error_code, transformer", [(1, 2)])
    def test_return_types(self, error_code, transformer):
        """Testing if the return type is the right one."""
        error_obj = None

        def set_data(temp):
            nonlocal error_obj
            error_obj = temp

        c_data = self.client.create_request()
        s_data = self.server.parser(c_data.model_dump_json(exclude_none=True))
        e_data = transformer(s_data)
        r_data = self.client.parser(e_data)

        assert r_data is None

        assert error_obj.code.value == error_code

    @pytest.mark.parametrize(
        "method,params",
        [
            [MethodsTest.ping, None],
            [MethodsTest.add, [1, 2, 3]],
            [MethodsTest.sub, [1, 2, 3]],
        ],
    )
    @pytest.mark.parametrize(
        "error_code, transformer",
        [
            [
                -32700,
                lambda data: {
                    "jsonrpc": "2.0",
                    "id": data.id,
                    "error": {"code": -32700, "message": "", "data": "k"},
                },
            ],
            [
                -32600,
                lambda data: {
                    "jsonrpc": "2.0",
                    "id": data.id,
                    "error": {"code": -32600, "message": "", "data": "k"},
                },
            ],
            [
                -32601,
                lambda data: {
                    "jsonrpc": "2.0",
                    "id": data.id,
                    "error": {"code": -32601, "message": "", "data": "k"},
                },
            ],
            [
                -32602,
                lambda data: {
                    "jsonrpc": "2.0",
                    "id": data.id,
                    "error": {"code": -32602, "message": "", "data": "k"},
                },
            ],
            [
                -32603,
                lambda data: {
                    "jsonrpc": "2.0",
                    "id": data.id,
                    "error": {"code": -32603, "message": "", "data": "k"},
                },
            ],
            [
                -32000,
                lambda data: {
                    "jsonrpc": "2.0",
                    "id": data.id,
                    "error": {"code": -32000, "message": "", "data": "k"},
                },
            ],
        ],
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
        s_data = self.server.parser(c_data.model_dump_json(exclude_none=True))
        e_data = transformer(s_data)
        r_data = self.client.parser(e_data)

        print(f"{r_data}")

        assert r_data is None
        assert data_obj is None
        assert error_obj.code.value == error_code

    def test_send_bulk(self):
        """Test is the Bulking works as intended."""
        cb_data = None

        def cb(data):
            print(f"data: {data}")
            nonlocal cb_data
            cb_data = data

        with self.client.batch():
            s_data = self.client.create_request(
                method=MethodsTest.add, callback=cb, params=[1, 2, 3]
            )
            assert s_data is None

            s_data = self.client.create_notification(method=MethodsTest.ping)
            assert s_data is None

        assert self.client.batch_size() == 2

        c_data = self.client.get_batch_data()
        # print(f"{s_data.model_dump_json(exclude_none=True)}")
        s_data = self.server.parser(c_data.model_dump_json(exclude_none=True))
        # print(data)
        assert len(s_data) == 1

        c_l_data = self.client.parser(s_data.model_dump_json(exclude_none=True))
        assert c_l_data is None
        assert cb_data == 6

    def test_received_bulk(self):
        """Test if the Bulking receiving works as intended."""
        pass

    @pytest.mark.parametrize(
        "error_code",
        # list(range(-32099, -32000 + 1)),
        [-32099, -32050, -32000],
    )
    def test_custom_error_response(self, error_code):
        """Test if the custom error response works as intended."""
        self.error_code = error_code
        msg = '{"jsonrpc": "2.0", "method": "error", "id": "12342"}'
        error_obj = self.client.parser(msg)
        obj_code = (
            error_obj.error.code
            if isinstance(error_obj.error.code, int)
            else error_obj.error.code.value
        )
        assert obj_code == error_code

    def test_unknown_id(self):
        """Test if the received jsonRps id is unknown."""
        pass
