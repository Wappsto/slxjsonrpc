slxjsonrpc
===============================================================================
The slxJsonRpc testers Read me.


Unsure
-------------------------------------------------------------------------------
  ...

Known Bugs
-------------------------------------------------------------------------------
 * If `exclude_unset` is false, the package will have: `"id":null` set. # Have an less nice workaround applied, with multiple RpcError's.
 * If `exclude_none` is True, the package will not have: `"result":null` set.
   Related: [Issue](https://github.com/pydantic/pydantic/issues/6465) [discussions](https://github.com/pydantic/pydantic/discussions/5461)

TODO List
-------------------------------------------------------------------------------
 * [ ] Add more test to get a 100%-ish testing coverage.
 * [x] Test Notification with unknown Method, and method Enum not set.
 * [x] Test Notification, where params set, when they should not be.
 * [x] Test Request with unknown Method, and method Enum not set.
 * [x] Test Request, where params set, when they should not be.
 * [x] Test response with unknown id
 * [x] Test RpcError, when no Error callback is set.
 * [x] Test if the Bulking receiving works as intended.
 * [x] Test with params as pydantic BaseModel.
 * [ ] Test where both client & server is used, at the same time.
 * [ ] Test if the IDs are in sequential order.
 * [ ] Make a [Specification](https://www.jsonrpc.org/specification) only test.
