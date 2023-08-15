slxjsonrpc
===============================================================================
The slxJsonRpc testers Read me.


Unsure
-------------------------------------------------------------------------------
  ...

Known Bugs
-------------------------------------------------------------------------------
 ...

TODO List
-------------------------------------------------------------------------------
 * [ ] Add more test to get a 100%-ish testing coverage.
 * [ ] Test Notification with unknown Method, and method Enum not set. jsonrpc.py:330
 * [ ] Test Notification, where params set, when they should not be.
 * [ ] Test Request with unknown Method, and method Enum not set. jsonrpc.py:348 schema/jsonrpc.py:131
 * [ ] Test Request, where params set, when they should not be.
 * [ ] Test response with unknown id
 * [ ] Test RpcError, when no Error callback is set.
 * [ ] Test if the Bulking receiving works as intended.
 * [ ] Test with params as pydantic BaseModel.
 * [ ] Test where both client & server is used, at the same time.
 * [ ] Test if the IDs are in sequential order.
