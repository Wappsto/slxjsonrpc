"""The pyTest Classes for testing the SlxJsonRpc Package."""
from enum import Enum

from typing import List

# from typing import Literal  # NOTE: Not possible in py37
from typing import Union

import pytest

from slxjsonrpc.schema import jsonrpc as jsonrpc_schema
from slxjsonrpc.schema.jsonrpc import MethodError

from pydantic import ValidationError
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
    point = "point"


class TestSchema:
    """Test the JsonRpc Schema."""

    def setup_method(self):
        """Setup the Schema mapping."""
        self.params_map = {
            MethodsTest.add: List[Union[int, float]],
            MethodsTest.sub: List[Union[int, float]],
            MethodsTest.ping: None,
            MethodsTest.point: Point,
        }
        jsonrpc_schema.set_params_map(
            self.params_map,
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
            ["point", Point(x=1, y=2), False],
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
        "method,the_id,result,data_out",
        [
            [
                MethodsTest.point,
                'hey_id',
                Point(x=1, y=2),
                '{"jsonrpc":"2.0","id":"hey_id","result":{"x":1,"y":2}}'
            ],
            [
                'something',
                'hey_id1',
                None,
                '{"jsonrpc":"2.0","id":"hey_id1","result":null}'
            ],
        ]
    )
    def test_Response(self, method, the_id, result, data_out):
        """For testing the Notification if no params where set."""
        jsonrpc_schema.set_id_mapping({the_id: method})
        jsonrpc_schema.set_result_map({method: type(result)})
        try:
            r_data = jsonrpc_schema.RpcResponse(
                jsonrpc=jsonrpc_schema.RpcVersion.v2_0,
                id=the_id,
                result=result,
            )

            assert data_out == r_data.model_dump_json()
        finally:
            jsonrpc_schema.set_id_mapping({})
            jsonrpc_schema.set_result_map({})

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
            ["point", Point(x=1, y=2), False],
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

    @pytest.mark.parametrize(
        "data_in,the_id,method,params",
        [
            (
                '{"jsonrpc":"2.0","method":"point","id":"some_id","params":{"x":1, "y": 2}}',
                'some_id',
                'point',
                Point(x=1, y=2),
            )
        ],
    )
    def test_request_deserializing(self, data_in, the_id, method, params):
        """Test deserializing of a json object."""
        data = jsonrpc_schema.RpcRequest.model_validate_json(data_in)

        assert data.method == method
        assert data.id == the_id
        assert data.params == params

    @pytest.mark.parametrize(
        "data_in,method,params",
        [
            (
                '{"jsonrpc":"2.0","method":"point","params":{"x":1, "y": 2}}',
                'point',
                Point(x=1, y=2),
            )
        ],
    )
    def test_notification_deserializing(self, data_in, method, params):
        """Test deserializing of a json object."""
        data = jsonrpc_schema.RpcNotification.model_validate_json(data_in)

        assert data.method == method
        assert data.params == params

    @pytest.mark.parametrize(
        "method,params,data_out",
        [
            [
                'method',
                'data',
                '{{"jsonrpc":"2.0","method":"method","id":"{}","params":"data"}}'
            ],
        ]
    )
    def test_no_mapping_Request(self, method, params, data_out):
        """For testing the Request if no params where set."""
        jsonrpc_schema.set_params_map({})
        try:
            r_data = jsonrpc_schema.RpcRequest(
                jsonrpc=jsonrpc_schema.RpcVersion.v2_0,
                method=method,
                params=params,
            )
            the_id = r_data.id
            data_string = data_out.format(the_id)
            assert data_string == r_data.model_dump_json()
        finally:
            jsonrpc_schema.set_params_map(self.params_map)

    @pytest.mark.parametrize(
        "method,params,data_out",
        [
            [
                'method',
                'data',
                '{"jsonrpc":"2.0","method":"method","params":"data"}'
            ],
        ]
    )
    def test_no_mapping_notification(self, method, params, data_out):
        """For testing the Notification if no params where set."""
        jsonrpc_schema.set_params_map({})
        try:
            r_data = jsonrpc_schema.RpcNotification(
                jsonrpc=jsonrpc_schema.RpcVersion.v2_0,
                method=method,
                params=params,
            )

            assert data_out == r_data.model_dump_json()
        finally:
            jsonrpc_schema.set_params_map(self.params_map)

    @pytest.mark.parametrize(
        "the_id,result,data_out",
        [
            [
                'hey_id',
                Point(x=1, y=2),
                '{"jsonrpc":"2.0","id":"hey_id","result":{"x":1,"y":2}}'
            ],
        ]
    )
    def test_no_mapping_Response(self, the_id, result, data_out):
        """For testing the Notification if no params where set."""
        jsonrpc_schema.set_id_mapping({})
        jsonrpc_schema.set_result_map({})

        r_data = jsonrpc_schema.RpcResponse(
            jsonrpc=jsonrpc_schema.RpcVersion.v2_0,
            id=the_id,
            result=result,
        )

        assert data_out == r_data.model_dump_json()

    @pytest.mark.parametrize(
        "the_id,result,data_out",
        [
            [
                'hey_id',
                Point(x=1, y=2),
                '{"jsonrpc":"2.0","id":"hey_id","result":{"x":1,"y":2}}'
            ],
        ]
    )
    def test_error_config_Response(self, the_id, result, data_out):
        """For testing the Notification if no params where set."""
        jsonrpc_schema.set_id_mapping({the_id: 'FAKE_METHOD'})
        jsonrpc_schema.set_result_map({'FAKE_METHOD': None})

        try:
            with pytest.raises(ValueError):
                jsonrpc_schema.RpcResponse(
                    jsonrpc=jsonrpc_schema.RpcVersion.v2_0,
                    id=the_id,
                    result=result,
                )
        finally:
            jsonrpc_schema.set_id_mapping({})
            jsonrpc_schema.set_result_map({})

    @pytest.mark.parametrize(
        "the_id,result,data_out",
        [
            [
                'hey_id',
                Point(x=1, y=2),
                '{"jsonrpc":"2.0","id":"hey_id","result":{"x":1,"y":2}}'
            ],
        ]
    )
    def test_missing_mapping_Response(self, the_id, result, data_out):
        """For testing the Notification if no params where set."""
        jsonrpc_schema.set_id_mapping({the_id: 'FAKE_METHOD'})
        jsonrpc_schema.set_result_map({MethodsTest.point: Point})

        try:
            with pytest.raises(ValueError):
                jsonrpc_schema.RpcResponse(
                    jsonrpc=jsonrpc_schema.RpcVersion.v2_0,
                    id=the_id,
                    result=result,
                )
        finally:
            jsonrpc_schema.set_id_mapping({})
            jsonrpc_schema.set_result_map({})
