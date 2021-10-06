"""The pyTest Classes for testing the SlxJsonRpc Package."""
from enum import Enum

from typing import List
# from typing import Literal  # NOTE: Not possible in py37
from typing import Union

from pydantic import parse_obj_as
from pydantic import ValidationError

import pytest

from slxjsonrpc import SlxJsonRpc
from slxjsonrpc.schema import jsonrpc as jsonrpc_schema


class MethodsTest(str, Enum):
    """The Enum of Methods for the SlXJsonRpc."""
    add = "add"
    ping = "ping"
    sub = "sub"


class TestSchema:
    """Test the JsonRpc Schema."""

    def setup_method(self):
        """Setup the Schema mapping."""
        jsonrpc_schema.params_mapping = {
            MethodsTest.add: List[Union[int, float]],
            MethodsTest.sub: List[Union[int, float]],
            MethodsTest.ping: None
        }

    @pytest.mark.parametrize(
        "method,data,not_exception",
        [
            ["add", [1, 2, 3], True],
            ["add", "pong", False],
            ["sub", [1, 2, 3], True],
            ["sub", "pong", False],
            ["ping", None, True],
            ["ping", [1, 2, 3], False],
            ["NOP", None, False],
            ["NOP", "Nop!", False],
        ]
    )
    def test_request(self, method, data, not_exception):
        """Test basic Request parsing."""
        jsonrpc_schema.RpcRequest.update_method(MethodsTest)
        strjson = {
            "id": "1",
            "jsonrpc": "2.0",
            "method": method,
        }
        if data:
            strjson["params"] = data
        print(strjson)
        try:
            r_data = parse_obj_as(jsonrpc_schema.RpcRequest, strjson)
        except ValidationError:
            if not_exception:
                raise
        else:
            if not not_exception:
                raise ValueError(f"Should Not have passed: {r_data}")

    @pytest.mark.parametrize(
        "method,data,not_exception",
        [
            ["add", [1, 2, 3], True],
            ["add", "pong", False],
            ["sub", [1, 2, 3], True],
            ["sub", "pong", False],
            ["ping", None, True],
            ["ping", [1, 2, 3], False],
            ["NOP", None, False],
            ["NOP", "Nop!", False],
        ]
    )
    def test_notifications(self, method, data, not_exception):
        """Test basic Notification parsing."""
        jsonrpc_schema.RpcNotification.update_method(MethodsTest)
        strjson = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if data:
            strjson["params"] = data
        print(strjson)
        try:
            r_data = parse_obj_as(jsonrpc_schema.RpcNotification, strjson)
        except ValidationError:
            if not_exception:
                raise
        else:
            if not not_exception:
                raise ValueError(f"Should Not have passed: {r_data}")

    @pytest.mark.parametrize(
        "_id",
        [
            ["hej"],
            ["øæasdnh"],
            ["he123\"}kjnf"],
        ]
    )
    def test_request_name(self, _id):
        """Test if the variable naming convention works."""
        method = "add"
        data = [1, 2, 3]
        jsonrpc_schema.RpcRequest.update_method(MethodsTest)
        jsonrpc_schema.RpcSetName(...)
        _id = "hej"
        strjson = {
            "id": _id,
            "jsonrpc": "2.0",
            "method": method,
        }
        if data:
            strjson["params"] = data

        r_data = parse_obj_as(jsonrpc_schema.RpcRequest, strjson)

        assert r_data.id == f"{jsonrpc_schema._session_id}_{_id}_{jsonrpc_schema._session_count}"


class TestSlxJsonRpc:
    """Test the communication between the SlxJsonRpc Server & Client."""

    def setup_method(self):
        """Setup the server & client instances of SlxJsonRpc."""
        jsonrpc_schema.RpcSetName(...)
        jsonrpc_schema.RpcRequest.update_method(MethodsTest)
        params = {
            MethodsTest.add: List[Union[int, float]],
            MethodsTest.sub: List[Union[int, float]],
            MethodsTest.ping: None
        }
        result = {
            MethodsTest.add: Union[int, float],
            MethodsTest.sub: Union[int, float],
            MethodsTest.ping: str  # Literal["pong"]
        }
        method_map = {
            MethodsTest.add: lambda data: sum(data),
            MethodsTest.sub: lambda data: data[0] - sum(data[1:]),
            MethodsTest.ping: lambda data: "pong"
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
