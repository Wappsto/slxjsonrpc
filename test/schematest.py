"""The pyTest Classes for testing the SlxJsonRpc Package."""
from enum import Enum

from typing import List
# from typing import Literal  # NOTE: Not possible in py37
from typing import Union

import pytest

from slxjsonrpc.schema import jsonrpc as jsonrpc_schema

from pydantic import parse_obj_as
from pydantic import ValidationError


class MethodsTest(str, Enum):
    """The Enum of Methods for the SlXJsonRpc."""
    add = "add"
    ping = "ping"
    sub = "sub"


class TestSchema:
    """Test the JsonRpc Schema."""

    def setup_method(self):
        """Setup the Schema mapping."""
        jsonrpc_schema.set_params_map({
            MethodsTest.add: List[Union[int, float]],
            MethodsTest.sub: List[Union[int, float]],
            MethodsTest.ping: None
        })

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
        jsonrpc_schema.rpc_set_name(...)
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
