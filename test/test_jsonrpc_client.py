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
                    '"message":"Internal server error.",'
                    '"data":"unsupported operand type(s) for -:'
                    ' \'str\' and \'int\'"}}'
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
                    '"message":"Internal server error.",'
                    '"data":"unsupported operand type(s) for -:'
                    ' \'str\' and \'int\'"}}'
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

    # @pytest.mark.parametrize(
    #     "method,params,result",
    #     [
    #         ["tweet", "Trumphy", "Trumphy"],
    #         ["tweet", 1, 1],
    #     ],
    # )
    # def test_notification_happy_flow(self, method, params, result):
    #     """Testing the Request Happy Flow."""
    #     c_data = self.client.create_notification(
    #         method=method,
    #         params=params
    #     )

    #     s_data = self.server.parser(c_data.model_dump_json(exclude_none=True))

    #     assert s_data is None
    #     assert self.tweet_data == result

    # @pytest.mark.parametrize(
    #     "error_code,data",
    #     [
    #         [-32700, '{"jsonrpc": "2.0", "method"'],
    #         [-32700, ""],
    #         [-32600, "[]"],
    #         [-32600, '{"foo": "boo"}'],
    #         [-32601, '{"jsonrpc": "2.0", "method": "NOWHERE!", "id": "1q"}'],
    #         [-32601, '{"jsonrpc": "2.0", "method": "NOWHERE!"}'],
    #         [-32602, '{"jsonrpc": "2.0", "method": "add", "id": "s1", "params": "NOP!"}'],
    #         [-32602, '{"jsonrpc": "2.0", "method": "add", "params": "NOP!"}'],
    #         [-32602, '{"jsonrpc": "2.0", "method": "add", "id": "s1"}'],
    #         [-32602, '{"jsonrpc": "2.0", "method": "add"}'],
    #         [-32000, '{"jsonrpc": "2.0", "method": "crash", "id": "12342"}'],
    #         [-32000, '{"jsonrpc": "2.0", "method": "crash"}'],
    #         # [-32099, ''],
    #     ],
    # )
    # def test_request_errors(self, data, error_code):
    #     """Testing the Request Happy Flow."""
    #     s_data = self.server.parser(data)
    #     print(f"{s_data}")
    #     assert s_data.error.code.value == error_code

    # @pytest.mark.skip(reason="TBW!")
    # @pytest.mark.parametrize("error_code, transformer", [(1, 2)])
    # def test_return_types(self, error_code, transformer):
    #     """Testing if the return type is the right one."""
    #     error_obj = None

    #     def set_data(temp):
    #         nonlocal error_obj
    #         error_obj = temp

    #     c_data = self.client.create_request()
    #     s_data = self.server.parser(c_data.model_dump_json(exclude_none=True))
    #     e_data = transformer(s_data)
    #     r_data = self.client.parser(e_data)

    #     assert r_data is None

    #     assert error_obj.code.value == error_code

    # @pytest.mark.parametrize(
    #     "method,params",
    #     [
    #         [MethodsTest.ping, None],
    #         [MethodsTest.add, [1, 2, 3]],
    #         [MethodsTest.sub, [1, 2, 3]],
    #     ],
    # )
    # @pytest.mark.parametrize(
    #     "error_code, transformer",
    #     [
    #         [
    #             -32700,
    #             lambda data: {
    #                 "jsonrpc": "2.0",
    #                 "id": data.id,
    #                 "error": {"code": -32700, "message": "", "data": "k"},
    #             },
    #         ],
    #         [
    #             -32600,
    #             lambda data: {
    #                 "jsonrpc": "2.0",
    #                 "id": data.id,
    #                 "error": {"code": -32600, "message": "", "data": "k"},
    #             },
    #         ],
    #         [
    #             -32601,
    #             lambda data: {
    #                 "jsonrpc": "2.0",
    #                 "id": data.id,
    #                 "error": {"code": -32601, "message": "", "data": "k"},
    #             },
    #         ],
    #         [
    #             -32602,
    #             lambda data: {
    #                 "jsonrpc": "2.0",
    #                 "id": data.id,
    #                 "error": {"code": -32602, "message": "", "data": "k"},
    #             },
    #         ],
    #         [
    #             -32603,
    #             lambda data: {
    #                 "jsonrpc": "2.0",
    #                 "id": data.id,
    #                 "error": {"code": -32603, "message": "", "data": "k"},
    #             },
    #         ],
    #         [
    #             -32000,
    #             lambda data: {
    #                 "jsonrpc": "2.0",
    #                 "id": data.id,
    #                 "error": {"code": -32000, "message": "", "data": "k"},
    #             },
    #         ],
    #     ],
    # )
    # def test_error_response(self, method, params, error_code, transformer):
    #     """Testing handling of the response, when receiving an RpcError."""
    #     error_obj = None
    #     data_obj = None

    #     def set_error(temp):
    #         nonlocal error_obj
    #         error_obj = temp

    #     def set_data(temp):
    #         nonlocal data_obj
    #         data_obj = temp

    #     c_data = self.client.create_request(
    #         method=method,
    #         params=params,
    #         callback=set_data,
    #         error_callback=set_error
    #     )
    #     s_data = self.server.parser(c_data.model_dump_json(exclude_none=True))
    #     e_data = transformer(s_data)
    #     r_data = self.client.parser(e_data)

    #     print(f"{r_data}")

    #     assert r_data is None
    #     assert data_obj is None
    #     assert error_obj.code.value == error_code

    # def test_received_bulk(self):
    #     """Test if the Bulking receiving works as intended."""
    #     pass

    # @pytest.mark.parametrize(
    #     "error_code",
    #     # list(range(-32099, -32000 + 1)),
    #     [-32099, -32050, -32000],
    # )
    # def test_custom_error_response(self, error_code):
    #     """Test if the custom error response works as intended."""
    #     self.error_code = error_code
    #     msg = '{"jsonrpc": "2.0", "method": "error", "id": "12342"}'
    #     error_obj = self.client.parser(msg)
    #     obj_code = (
    #         error_obj.error.code
    #         if isinstance(error_obj.error.code, int)
    #         else error_obj.error.code.value
    #     )
    #     assert obj_code == error_code

    # def test_unknown_id(self):
    #     """Test if the received jsonRps id is unknown."""
    #     pass

    # @pytest.mark.parametrize(
    #     "exclude_unset",
    #     [
    #         True,
    #         False,
    #     ],
    # )
    # @pytest.mark.parametrize(
    #     "exclude_none", [
    #         True,
    #         # False,
    #     ],
    # )
    # @pytest.mark.parametrize(
    #     "exclude_defaults", [
    #         True,
    #         False,
    #     ],
    # )
    # @pytest.mark.parametrize(
    #     "method,params,data_out",
    #     [
    #         [
    #             "NOP!",
    #             [1, 2, 3],
    #             ' '
    #         ],
    #     ],
    # )
    # def test_notificatest_input_errortion(
    #     self,
    #     method,
    #     params,
    #     data_out,
    #     exclude_unset,
    #     exclude_none,
    #     exclude_defaults,
    # ):
    #     """Testing the Request Happy Flow."""
    #     c_data = self.client.create_notification(
    #         method=method,
    #         params=params,
    #     )

    #     assert c_data is not None

    #     r_data = c_data.model_dump_json(
    #         exclude_unset=exclude_unset,
    #         exclude_none=exclude_none,
    #         exclude_defaults=exclude_defaults,
    #     )

    #     assert r_data == data_out

    def test_callback_example(self):
        """Just to get the code Coverage for the function example."""
        slxjsonrpc.jsonrpc.method_callback_example(1)
