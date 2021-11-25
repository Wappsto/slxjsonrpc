slxjsonrpc
===============================================================================

SlxJsonRpc is a JsonRpc helper class, that uses pydantic.

SlxJsonRpc keep track of the JsonRpc schema, and procedure for each method.
It also ensures to route each message to where it is expected.

SlxJsonRpc is build to be both a JsonRpc server & client.
To enable the JsonRpc-server, the method_map need to be given.

### Installation using pip

The slxjsonrpc package can be installed using PIP (Python Package Index) as follows:

```bash
$ pip install slxjsonrpc
```

### Use case Examples

The given use case show how to use the slxJsonRpc Package.
It expected that you have a send & a receive function/method to transport
the Json RPC messages to and from the package.

The Client example code:
```python
from typing import List, Union, Literal

from enum import Enum
import slxjsonrpc


def send(data: str) -> None: ...


def receive() -> Union[str, bytes, dict]: ...


class MethodList(str, Enum):
    ADD = "add"
    PING = "ping"


params = {
    MethodList.ADD: List[Union[int, float]],
    MethodList.PING: None,
}

result = {
    MethodList.ADD: Union[int, float],
    MethodList.PING: Literal["pong"]
}

client_jsonrpc = slxjsonrpc.SlxJsonRpc(
    methods=MethodsList,
    result=result,
    params=params,
)

ok = None


def reply(reply_data):
    nonlocal ok
    ok = reply_data  # Will be "pong"


ping_package = client_jsonrpc.create_request(method=MethodList.PING, callback=reply)
send(ping_package.json(exclude_none=True))
data = receive()
client_jsonrpc.parser(data)

print(f"OK: {ok}")
```


The Server example code:
```python
from typing import List, Union, Literal

from enum import Enum
import slxjsonrpc


def send(data: str) -> None: ...


def receive() -> Union[str, bytes, dict]: ...


class MethodList(str, Enum):
    ADD = "add"
    PING = "ping"


params = {
    MethodList.ADD: List[Union[int, float]],
    MethodList.PING: None,
}

result = {
    MethodList.ADD: Union[int, float],
    MethodList.PING: Literal["pong"]
}


method_map = {
    MethodList.ADD: lambda data: sum(data),
    MethodList.PING: lambda data: "pong",
}


server_jsonrpc = slxjsonrpc.SlxJsonRpc(
    methods=MethodsList,
    result=result,
    params=params,
    method_cb=method_map,
)

data = receive()
return_data = server_jsonrpc.parser(data)
if return_data:
    send(return_data.json(exclude_none=True))
```


License
-------------------------------------------------------------------------------

This project is licensed under the Apache License 2.0 - see the [LICENSE.md](LICENSE.md) file for details.


Known Bugs
-------------------------------------------------------------------------------
 * Can not have 2 independent slxJsonRpcs running in same code base.


TODO List
-------------------------------------------------------------------------------
**Code base**
 * [ ] Add more/better logging logs.
 * [x] Enforce the result Schema. schema/jsonrpc.py:217-225
 * [x] Push to pip.
 * [ ] Refactor so the same code can have multiple independent slxJsonRpc.
 * [x] Use case Examples.

**Tests**
 * [ ] Add more test to get a 100%-ish testing coverage.
 * [ ] Test Notification with unknown Method, and method Enum not set. jsonrpc.py:330
 * [ ] Test Notification, where params set, when they should not be.
 * [ ] Test Request with unknown Method, and method Enum not set. jsonrpc.py:348 schema/jsonrpc.py:131
 * [ ] Test Request, where params set, when they should not be.
 * [ ] Test response with unknown id
 * [ ] Test RpcError, when no Error callback is set.
