"""The SlxJsonRpc Package."""
from slxjsonrpc.jsonrpc import SlxJsonRpc

from slxjsonrpc.schema.jsonrpc import RpcBatch
from slxjsonrpc.schema.jsonrpc import RpcError
from slxjsonrpc.schema.jsonrpc import RpcNotification
from slxjsonrpc.schema.jsonrpc import RpcRequest
from slxjsonrpc.schema.jsonrpc import RpcResponse

__all__ = [
    'SlxJsonRpc',
    'RpcBatch',
    'RpcError',
    'RpcNotification',
    'RpcRequest',
    'RpcResponse',
]

__version__ = "v0.01"
