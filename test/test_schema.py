"""The pyTest Classes for testing the SlxJsonRpc Package."""
from enum import Enum

from typing import List

# from typing import Literal  # NOTE: Not possible in py37
from typing import Union

import pytest

from slxjsonrpc.schema import jsonrpc as jsonrpc_schema
from slxjsonrpc.schema.jsonrpc import MethodError

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
        jsonrpc_schema.set_params_map(
            {
                MethodsTest.add: List[Union[int, float]],
                MethodsTest.sub: List[Union[int, float]],
                MethodsTest.ping: None,
            },
        )

    @pytest.mark.parametrize(
        "method,data,should_trigger_exception",
        [
            ["add", [1, 2, 3], False],
            ["add", "pong", True],
            ["sub", [1, 2, 3], False],
            ["sub", "pong", True],
            ["ping", None, False],
            ["ping", [1, 2, 3], True],
            ["NOP", None, True],
            ["NOP", "Nop!", True],
        ],
    )
    def test_request(self, method, data, should_trigger_exception):
        """Test basic Request parsing."""
        jsonrpc_schema.RpcRequest.update_method(MethodsTest)
        strJson = {
            "id": "1",
            "jsonrpc": "2.0",
            "method": method,
        }
        if data:
            strJson["params"] = data
        print(strJson)

        try:
            r_data = jsonrpc_schema.RpcRequest.model_validate(strJson)
        except (ValidationError, MethodError):
            if not should_trigger_exception:
                raise
        else:
            if should_trigger_exception:
                raise ValueError(f"Should Not have passed: {r_data}")

    @pytest.mark.parametrize(
        "method,data,should_trigger_exception",
        [
            ["add", [1, 2, 3], False],
            ["add", "pong", True],
            ["sub", [1, 2, 3], False],
            ["sub", "pong", True],
            ["ping", None, False],
            ["ping", [1, 2, 3], True],
            ["NOP", None, True],
            ["NOP", "Nop!", True],
        ],
    )
    def test_notifications(self, method, data, should_trigger_exception):
        """Test basic Notification parsing."""
        jsonrpc_schema.RpcNotification.update_method(MethodsTest)
        strJson = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if data:
            strJson["params"] = data
        print(strJson)

        try:
            r_data = jsonrpc_schema.RpcNotification.model_validate(strJson)
        except (ValidationError, MethodError):
            if not should_trigger_exception:
                raise
        else:
            if should_trigger_exception:
                raise ValueError(f"Should Not have passed: {r_data}")

    @pytest.mark.parametrize(
        "_id",
        [
            "hej",
            "øæasdnh",
            "he123\"}kjnf",
        ]
    )
    def test_response_id(self, _id):
        """Test if the variable naming convention works."""
        method = "add"
        data = [1, 2, 3]
        jsonrpc_schema.RpcRequest.update_method(MethodsTest)
        jsonrpc_schema.rpc_set_name(...)
        strJson = {
            "id": _id,
            "jsonrpc": "2.0",
            "method": method,
        }
        if data:
            strJson["params"] = data

        r_data = jsonrpc_schema.RpcRequest.model_validate(strJson)

        assert r_data.id == _id

    @pytest.mark.parametrize(
        "_id",
        [
            "hej",
            "øæasdnh",
            "he123\"}kjnf",
        ]
    )
    def test_emitted_id(self, _id):
        """Test if the variable naming convention works."""
        method = "add"
        data = [1, 2, 3]
        jsonrpc_schema.RpcRequest.update_method(MethodsTest)
        jsonrpc_schema.rpc_set_name(_id)

        r_data = jsonrpc_schema.RpcRequest(
            method=method,
            params=data,
        )

        assert r_data.id == f"{jsonrpc_schema._session_id}_{_id}_{jsonrpc_schema._session_count}"

    @pytest.mark.parametrize(
        "_id",
        [
            "hej",
            "øæasdnh",
            "he123\"}kjnf",
        ]
    )
    def test_given_id(self, _id):
        """Test if the variable naming convention works."""
        method = "add"
        data = [1, 2, 3]
        jsonrpc_schema.RpcRequest.update_method(MethodsTest)
        jsonrpc_schema.rpc_set_name(...)

        r_data = jsonrpc_schema.RpcRequest(
            method=method,
            params=data,
            id=_id,
        )

        assert r_data.id == _id
