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
 * [ ] Refactor so the same code can have multiple independent slxJsonRpc.
 * [ ] Check if custom validation exceptions will make the code simpler?
 * [x] No RpcError on Notifications.
 * [ ] RpcResponse should always have the `result`-key.
 * [ ] RpcError should always have the `id`-key.
