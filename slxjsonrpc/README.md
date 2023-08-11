slxjsonrpc
===============================================================================
The slxJsonRpc developers Read me.


Unsure
-------------------------------------------------------------------------------
 * Is it required to return a batch of 1, if it was received as batch of 1?


Known Bugs
-------------------------------------------------------------------------------
 * Can not have 2 independent slxJsonRpc running in same code base.
 * If `exclude_unset` is false, the package will have: `"id":null` set.
 * If `exclude_none` is True, the package will not have: `"result":null` set.


TODO List
-------------------------------------------------------------------------------
**Code base**
 * [ ] Add more/better logging logs.
 * [x] Enforce the result Schema. schema/jsonrpc.py:217-225
 * [x] Push to pip.
 * [ ] Refactor so the same code can have multiple independent slxJsonRpc.
 * [x] Use case Examples.
 * [ ] Check if custom validation exceptions will make the code simpler?
