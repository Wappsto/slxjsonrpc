"""The pyTest Classes for testing the SlxJsonRpc Package."""
from enum import Enum

from typing import Any
from typing import List

# from typing import Literal  # NOTE: Not possible in py37
from typing import Union

import pytest

import slxjsonrpc


# slxjsonrpc.schema.jsonrpc._id_gen = lambda *args, **kwargs: 'the_id'

class MethodsTest(str, Enum):
    """The Enum of Methods for the SlXJsonRpc."""

    add = "add"
    ping = "ping"
    sub = "sub"
    crash = "crash"
    tweet = "tweet"
    error = "error"


class TestSlxJsonRpc:
    """Test the communication between the SlxJsonRpc Server & Client."""

    def setup_method(self):
        """Setup the server & client instances of SlxJsonRpc."""
        params = {
            MethodsTest.add: List[Union[int, float]],
            MethodsTest.sub: List[Union[int, float]],
            MethodsTest.ping: None,
            MethodsTest.crash: None,
            MethodsTest.tweet: Any,
            MethodsTest.error: Any,
        }
        result = {
            MethodsTest.add: Union[int, float],
            MethodsTest.sub: Union[int, float],
            MethodsTest.ping: str,  # Literal["pong"]
            MethodsTest.crash: int,
            MethodsTest.tweet: None,
            MethodsTest.error: None,
        }

        self.client = slxjsonrpc.SlxJsonRpc(
            methods=MethodsTest,
            result=result,
            params=params,
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
            # False,
        ],
    )
    @pytest.mark.parametrize(
        "exclude_defaults", [
            True,
            False,
        ],
    )
    @pytest.mark.parametrize(
        "method,params,data_out",
        [
            [
                "ping",
                None,
                '{"jsonrpc":"2.0","method":"ping","id":"the_id"}',
            ],
            [
                "add",
                [1, 2, 3],
                '{"jsonrpc":"2.0","method":"add","id":"the_id","params":[1,2,3]}',
            ],
            [
                "sub",
                [1, 2, 3],
                '{"jsonrpc":"2.0","method":"sub","id":"the_id","params":[1,2,3]}'
            ],
        ],
    )
    def test_request(
        self,
        method,
        params,
        data_out,
        exclude_unset,
        exclude_none,
        exclude_defaults,
    ):
        """Testing the Request Happy Flow."""
        c_data = self.client.create_request(
            method=method,
            params=params,
            callback=lambda data: None
        )

        assert c_data is not None

        c_data.id = 'the_id'

        r_data = c_data.model_dump_json(
            exclude_unset=exclude_unset,
            exclude_none=exclude_none,
            exclude_defaults=exclude_defaults,
        )

        assert r_data == data_out

    @pytest.mark.parametrize(
        "data_in",
        [
            '{"jsonrpc":"2.0","id":"NeverUsedId","result":"pong"}',
        ],
    )
    def test_unknown_response(
        self,
        data_in,
    ):
        """For triggering the unknown ID in the response logic."""
        c_data = self.client.parser(
            data=data_in
        )
        assert c_data is None

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
            # False,
        ],
    )
    @pytest.mark.parametrize(
        "exclude_defaults", [
            True,
            False,
        ],
    )
    @pytest.mark.parametrize(
        "method,params,data_out",
        [
            [
                "ping",
                None,
                '{"jsonrpc":"2.0","method":"ping"}',
            ],
            [
                "add",
                [1, 2, 3],
                '{"jsonrpc":"2.0","method":"add","params":[1,2,3]}',
            ],
            [
                "sub",
                [1, 2, 3],
                '{"jsonrpc":"2.0","method":"sub","params":[1,2,3]}'
            ],
        ],
    )
    def test_notification(
        self,
        method,
        params,
        data_out,
        exclude_unset,
        exclude_none,
        exclude_defaults,
    ):
        """Testing the notification Happy Flow."""
        c_data = self.client.create_notification(
            method=method,
            params=params,
        )

        assert c_data is not None

        r_data = c_data.model_dump_json(
            exclude_unset=exclude_unset,
            exclude_none=exclude_none,
            exclude_defaults=exclude_defaults,
        )

        assert r_data == data_out

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
            # False,
        ],
    )
    @pytest.mark.parametrize(
        "exclude_defaults", [
            True,
            False,
        ],
    )
    @pytest.mark.parametrize(
        "method_params,data_out",
        [
            [
                [("ping", None), ("add", [1, 2, 3]), ("sub", [1, 2, 3])],
                (
                    '[{"jsonrpc":"2.0","method":"ping"},'
                    '{"jsonrpc":"2.0","method":"add","params":[1,2,3]},'
                    '{"jsonrpc":"2.0","method":"sub","params":[1,2,3]}]'
                ),
            ],
            [
                [("ping", None),],
                (
                    '{"jsonrpc":"2.0","method":"ping"}'
                ),
            ],
            [
                [],
                None,
            ],
        ],
    )
    def test_bulk(
        self,
        method_params,
        data_out,
        exclude_unset,
        exclude_none,
        exclude_defaults,
    ):
        """Test is the Bulking works as intended."""
        with self.client.batch():
            for method, params in method_params:
                c_data = self.client.create_notification(
                    method=method,
                    params=params,
                )
                assert c_data is None

        data = self.client.get_batch_data()

        if data_out is None:
            assert data is None
            return

        if isinstance(data, slxjsonrpc.RpcBatch):
            assert data[0]
            count = 0
            for x in data:
                count += 1
            assert count == len(data)

        r_data = data.model_dump_json(
            exclude_unset=exclude_unset,
            exclude_none=exclude_none,
            exclude_defaults=exclude_defaults,
        )

        assert r_data == data_out

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
            # False,
        ],
    )
    @pytest.mark.parametrize(
        "exclude_defaults", [
            True,
            False,
        ],
    )
    @pytest.mark.parametrize(
        "method_params,mp_thread,data_out",
        [
            [
                [("ping", None), ("add", [1, 2, 3])],
                ("sub", [1, 2, 3]),
                (
                    '[{"jsonrpc":"2.0","method":"ping"},'
                    '{"jsonrpc":"2.0","method":"add","params":[1,2,3]},'
                    '{"jsonrpc":"2.0","method":"sub","params":[1,2,3]}]'
                ),
            ],
        ],
    )
    def test_bulk_treaded(
        self,
        method_params,
        mp_thread,
        data_out,
        exclude_unset,
        exclude_none,
        exclude_defaults,
    ):
        """Test is the Bulking works as intended."""
        with self.client.batch():
            for method, params in method_params:
                c_data = self.client.create_notification(
                    method=method,
                    params=params,
                )
                assert c_data is None

        t_data = self.client.create_notification(
            method=mp_thread[0],
            params=mp_thread[1],
        )

        data = self.client.get_batch_data(t_data)

        if data_out is None:
            assert data is None
            return

        if isinstance(data, slxjsonrpc.RpcBatch):
            assert data[0]
            count = 0
            for x in data:
                count += 1
            assert count == len(data)

        r_data = data.model_dump_json(
            exclude_unset=exclude_unset,
            exclude_none=exclude_none,
            exclude_defaults=exclude_defaults,
        )

        assert r_data == data_out

    # @pytest.mark.parametrize(  # NOTE: Breaks because of the ig_gen hack
    #     "exclude_unset",
    #     [
    #         True,
    #         False,
    #     ],
    # )
    @pytest.mark.parametrize(
        "exclude_none", [
            True,
            # False,
        ],
    )
    @pytest.mark.parametrize(
        "exclude_defaults", [
            True,
            False,
        ],
    )
    @pytest.mark.parametrize(
        "method,params,data_out,data_in,code",
        [
            [
                "crash",
                None,
                '{"jsonrpc":"2.0","method":"crash","id":"the_id"}',
                (
                    '{"id":"the_id","jsonrpc":"2.0","error":'
                    '{"code":-32000,'
                    '"message":"Internal server error."}}'
                ),
                -32000,
            ],
            [
                "crash",
                None,
                '{"jsonrpc":"2.0","method":"crash","id":"the_id"}',
                (
                    '{"id":"the_id","jsonrpc":"2.0","error":'
                    '{"code":-32000,'
                    '"message":"Internal server error."}}'
                ),
                None,
            ],
        ],
    )
    def test_request_error_callback(
        self,
        method,
        params,
        data_out,
        data_in,
        # exclude_unset,  # NOTE: Breaks because of the ig_gen hack
        exclude_none,
        exclude_defaults,
        code,
    ):
        """."""
        backup = slxjsonrpc.schema.jsonrpc._id_gen
        slxjsonrpc.schema.jsonrpc._id_gen = lambda *args, **kwargs: 'the_id'
        error = None

        def err_cb(error_model) -> None:
            nonlocal error
            error = error_model

        c_data = self.client.create_request(
            method=method,
            params=params,
            callback=lambda data: None,
            error_callback=err_cb if code is not None else None,
        )

        slxjsonrpc.schema.jsonrpc._id_gen = backup

        assert c_data is not None

        print(c_data)

        r_data = c_data.model_dump_json(
            # exclude_unset=exclude_unset,  # NOTE: Breaks because of the ig_gen hack
            exclude_none=exclude_none,
            exclude_defaults=exclude_defaults,
        )

        assert r_data == data_out

        data = self.client.parser(data_in)

        assert data is None

        if code is None:
            return

        assert error is not None
        assert error.code == code

    def test_callback_example(self):
        """Just to get the code Coverage for the function example."""
        slxjsonrpc.jsonrpc.method_callback_example(1)

    @pytest.mark.parametrize(
        "method,params",
        [
            [
                "ping",
                'Shoudl\'tBeHere',
            ],
        ],
    )
    def test_misconfigured_request(
        self,
        method,
        params,
    ):
        """Testing the Request Happy Flow."""
        with pytest.raises(ValueError):
            self.client.create_request(
                method=method,
                params=params,
                callback=lambda data: None
            )

    @pytest.mark.parametrize(
        "method,params",
        [
            [
                "ping",
                'Shoudl\'tBeHere',
            ],
        ],
    )
    def test_misconfigured_notification(
        self,
        method,
        params,
    ):
        """Testing the Request Happy Flow."""
        with pytest.raises(ValueError):
            self.client.create_notification(
                method=method,
                params=params,
            )
