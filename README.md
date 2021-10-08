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

License
-------------------------------------------------------------------------------

This project is licensed under the Apache License 2.0 - see the [LICENSE.md](LICENSE.md) file for details.



Known Bugs
-------------------------------------------------------------------------------
* Can not receive a Bulked JsonRpc List. Yet.


TODO List
-------------------------------------------------------------------------------
* [ ] Use case Examples.
* [ ] Enforce the result Schema.
* [ ] Push to pip.
* [ ] Test Bulk.
* [ ] Add more test to get a 100%-ish testing coverage.
