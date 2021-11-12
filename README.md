slxjsonrpc
===============================================================================

SlxJsonRpc is a JsonRpc helper class, that uses pydantic.

SlxJsonRpc keep track of the JsonRpc schema, and procedure for each method.
It also ensures to route each message to where it is expected.

SlxJsonRpc is build to be both that JsonRpc server & client.
To enable the JsonRpc-server, the method_map need to be given.

### Installation using pip

The slxjsonrpc package can be installed using PIP (Python Package Index) as follows:

```bash
$ pip install slxjsonrpc
```

### Use case Examples



License
-------------------------------------------------------------------------------

This project is licensed under the Apache License 2.0 - see the [LICENSE.md](LICENSE.md) file for details.



Known Bugs
-------------------------------------------------------------------------------
...


TODO List
-------------------------------------------------------------------------------
* [ ] Use case Examples.
* [ ] Add more/better logging logs.
* [x] Enforce the result Schema. schema/jsonrpc.py:217-225
* [ ] Push to pip.
* [ ] Add more test to get a 100%-ish testing coverage.
* [ ] Test response with unknown id
* [ ] Test Request with unknown Method, and method Enum not set. jsonrpc.py:348 schema/jsonrpc.py:131
* [ ] Test Notification with unknown Method, and method Enum not set. jsonrpc.py:330
* [ ] Test RpcError, when no Error callback is set.
* [ ] Test Request, where params set, when they should not be.
* [ ] Test Notification, where params set, when they should not be.
