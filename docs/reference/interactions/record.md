# Interaction Records

Interaction records are deliberately small. `InteractionRecord` represents an
explicit relationship, `ContactRecord` groups computed contact regions for one
element pair, and `ModifierRecord` stores one explicitly directed modifier.

The model owns records and runtime graph edges store only their GUID
references. Graph nodes use element GUIDs as stable keys. The graph is derived
from the records during model loading rather than serialized independently.
Use model methods to create, query, replace, or remove records so connectivity
and cache invalidation remain synchronized.

Record queries are the single model-level access path. Use
`contact_records`, `contact_records_between`, `modifier_records`,
`modifier_records_between`, or `modifier_records_for`, and then access the
record's `contacts` or `modifier`. The model intentionally does not provide a
parallel set of payload-only queries because those would discard record
identity, ownership, and modifier direction.

`ModifierRecord.order` is local to its target element and controls final
geometry evaluation. Use `Model.reorder_modifier_records` instead of mutating
order values directly so cache invalidation remains synchronized.

::: compas_model.interactions.record
