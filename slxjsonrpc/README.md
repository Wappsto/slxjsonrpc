slxjsonrpc
===============================================================================
The slxJsonRpc developers Read me.


[Specification](https://www.jsonrpc.org/specification)


Server Flow
-------------------------------------------------------------------------------

```
Network                          SlxJsonRpc                     User-Program
-------------------------------------------------------------------------------

Request                       +-------------+
 ---------------------------->| Deserialize |----------------->+-------------+
                              |   Analyse   |                  |             |
                              | - - - - - - |                  |   Callback  |
Response                      |   Analyse   |                  |             |
  <---------------------------|  Serialize  |<-----------------+-------------+
                              +-------------+
```

Client Flow
-------------------------------------------------------------------------------

```
Network                          SlxJsonRpc                     User-Program
-------------------------------------------------------------------------------

Request                       +-------------+                  User-Request
 <----------------------------|   Analyse   |<-----------------------+--------
                              |  Serialize  |                        | (Set)
                              | - - - - - - |                        v
Response                      | Deserialize |                 +-------------+
 -----------------------------|   Analyse   |---------------->|   Callback  |
                              +-------------+                 +-------------+
```


Unsure
-------------------------------------------------------------------------------
 * Is it required to return a batch of 1, if it was received as batch of 1?


Known Bugs
-------------------------------------------------------------------------------
 * Can not have 2 independent slxJsonRpc running in same code base.
 * If `exclude_unset` is false, the package will have: `"id":null` set. # Have an less nice workaround applied, with multiple RpcError's.
 * If `exclude_none` is True, the package will not have: `"result":null` set.
   Related: [Issue](https://github.com/pydantic/pydantic/issues/6465) [discussions](https://github.com/pydantic/pydantic/discussions/5461)


TODO List
-------------------------------------------------------------------------------
**Code base**
 * [ ] Add more/better logging logs.
 * [x] Enforce the result Schema. schema/jsonrpc.py:217-225
 * [x] Push to pip.
 * [ ] Refactor so the same code can have multiple independent slxJsonRpc.
 * [x] Use case Examples.
 * [ ] Check if custom validation exceptions will make the code simpler?
 * [ ] No RpcError on Notifications.
