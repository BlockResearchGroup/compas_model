# Contacts

`Contact` requires a `PlanarRegion`, which is the single authoritative contact
geometry. The region contains the oriented contact frame; if callers do not
provide one when constructing the region, `PlanarRegion` computes a best-fit
frame from its exterior boundary. Mesh and BRep representations are derived
and cached on demand.

::: compas_model.interactions.contact
