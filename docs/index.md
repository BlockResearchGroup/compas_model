# COMPAS Model

COMPAS Model is a general-purpose model data structure for AEC applications.
It organizes geometric elements in a spatial hierarchy, connects them through
an interaction graph, and supports overlapping collections for classifications
that do not belong in the hierarchy.

The package intentionally provides context-free infrastructure. Domain types
such as beams, walls, or assembly-specific blocks belong in downstream
packages such as COMPAS Timber and COMPAS DEM.

## Start here

1. [Install the core package and any optional capabilities](installation.md).
2. [Build and inspect a small model](tutorial.md).
3. Browse the [executable examples](examples/index.md).
4. Consult the [API reference](reference/compas_model.models.md) for detailed
   interfaces.

Collision, contact, BRep, sectioning, clipping, and visualization facilities
are documented separately because their dependencies and numerical semantics
differ from the core model infrastructure.
