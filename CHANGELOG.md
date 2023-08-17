v0.9.2 (August X, 2023)
===============================================================================

## Added
 * RcpBatch is now iterable and behave more list a list.

## Fixed
 * Type hinting errors.
 * Most issues where the wrong combo of `exclude_unset` & `exclude_none` given to `model_dump_json` would result in a invalid JsonRpc.

## Changed
 * Notifications can now not trigger an Error Rpc reply. as per the specification.


v0.9.1 (August 4, 2023)
===============================================================================

## Fixed
 * Type hinting errors.
 * A method to param mapping error.

v0.9.0 (August 3, 2023)
===============================================================================

## Changed
 * Now using Pydantic version 2.
 * Now require python 3.7 or later.

v0.8.2 (December 13, 2021)
===============================================================================

## Added
 * Change-log

## Changed
 * How `create_request` adds a Result reply handling. So now it uses `_add_result_handling`, which mean it will be easier to hook into for work-a-rounds.


v0.8.1 (November 25, 2021)
===============================================================================

## Fixed
 * Type hinting errors.


v0.8.0 (November 12, 2021)
===============================================================================
## Added
 * First Release.
