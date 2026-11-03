# Interactions

Interaction records are owned and serialized by the model. The interaction
graph indexes which element pairs are connected, but its internal edge
attributes are not the public storage API. The graph is a standard COMPAS
`Graph` keyed by element GUIDs and is rebuilt from the records when a model is
loaded; it is not duplicated in serialized model data.

- [Contacts](interactions/contact.md)
- [Interaction records](interactions/record.md)
