# Model viewer infrastructure

The model viewer integration separates domain geometry from render geometry.
Elements keep their original Mesh or BRep representation for modelling and
precise computations. `RenderGeometry` is a backend-neutral, CPU-side snapshot
containing arrays suitable for interactive rendering; it is not serialized as
part of an element and is not used for collision, contact, section, or clip
calculations.

## Face and boundary representation

Filled surfaces and visible boundaries are stored independently:

- `vertices` and `triangles` describe filled faces;
- `line_vertices` contains explicit pairs of visible boundary endpoints;
- `point_vertices` contains optional display points.

This distinction prevents the internal diagonals introduced by triangulation
from appearing as model edges.

For a Mesh, every original face is triangulated for filled rendering, while
the line buffer is built only from `Mesh.edges()`. Concave polygon faces are
therefore rendered with triangles without displaying their triangulation
diagonals.

For a BRep, `render_geometry_from_brep` uses the backend's `to_viewmesh`
operation. With COMPAS OCC this reuses Open CASCADE's face tessellation and the
separately sampled topological edge polylines. The tessellation approximates
curved surfaces according to the backend's linear and angular deflection, but
the displayed line buffer follows BRep edge boundaries rather than triangle
edges.

`ElementObject` computes this representation once when the scene object is
created and supplies it directly to COMPAS Viewer's buffer-building methods.

## Model viewer controller

`ModelViewer` is the integration point for displaying an entire model. It owns
one shared `RenderGeometryCache` and one shared `RenderSettings` instance, adds
the model and its elements to COMPAS Viewer, and indexes the resulting concrete
`ElementObject` instances by element GUID.

```python
from compas_model.viewer import ModelViewer

controller = ModelViewer(model)
controller.select([element], clear=True)
controller.hide([other_element])
controller.refresh(element)
controller.show_viewer()
```

The controller traverses `Model.tree` and creates the same parent-child
relationships in the COMPAS scene. The model tree remains authoritative; no
second hierarchy or intermediate element-view objects are created. Scene
objects can be retrieved with `object_for_element` or `object_for_guid` for
tree widgets and property inspectors.

`refresh` updates one object's render geometry, while `refresh_all` checks all
objects against their element geometry revisions. Selection and visibility
operate directly on the concrete scene objects. On Python 3.14, automatic
viewer construction applies the local COMPAS Viewer 2.0.1 configuration
compatibility patch before instantiating the viewer.

### Model navigation projections

By default, `ModelViewer` replaces COMPAS Viewer's generic scene form with a
`ModelNavigationForm` containing four views of the same data:

- **Hierarchy** follows the authoritative parent-child structure in
  `Model.tree`.
- **Collections** shows named, potentially overlapping element sets and an
  `Uncollected` branch.
- **Types** groups element references by their concrete Python class.
- **Interactions** projects interaction-graph edges as element pairs, with
  computed planar contact regions and modifiers below them.

These are transient Qt projections, not additional model containers. Element
items store GUIDs and resolve through `ModelViewer`; interaction items store
graph-edge and region indices and resolve through `Model.graph`. Consequently,
changing a projection never changes model ownership, group membership, or the
interaction graph. Rebuilding the tabs with `update(refresh=True)` reflects
structural changes made through the model API.

`Group` and `Collection` intentionally have different semantics. A `Group` is
an element in `Model.tree`: it expresses assembly or containment, has one
hierarchical parent, and may own child elements. A `Collection` is model data
outside that hierarchy. It stores ordered element GUID references, can overlap
other collections, and has no geometry, transformation, BVH entry, or
interaction-graph node.

```python
facade = model.add_collection("Facade", attributes={"discipline": "architecture"})
phase_1 = model.add_collection("Phase 1")

facade.add_elements([wall_a, wall_b, window])
phase_1.add_elements([wall_a, column, slab])
```

Collections are serialized with the model. Removing an element removes its
membership from every collection; removing a collection does not remove its
elements. `collections_for_element` resolves overlapping membership.

The element projections support multiple selection. Tree selections update the
`ElementObject.is_selected` flags through the controller, while `update()`
synchronizes viewport selections across all projections. The visibility column
updates `ElementObject.show`. Changing a branch checkbox applies the same state
to all descendant element objects.

Synthetic projection headings are bulk controls rather than decorative labels.
Selecting a heading such as `MeshElement` selects every element referenced by
that type branch. Its visibility checkbox shows or hides the complete branch
and displays a partial state when member visibility is mixed. The same behavior
applies to collection headings and the synthetic `Uncollected` heading.

Selecting a contact pair or region selects both incident elements in the
viewport and sends the contact selection to the inspector. Contacts remain
derived interaction data: they are deliberately not inserted into
`Model.tree`. The interaction view currently exposes computed contacts; other
edge payloads and transient collision-query result sets can be added as
separate projections without conflating them with persistent element
hierarchy.

Computed contacts are rendered by a `ContactLayer`. Every planar contact
region has its own scene object and picking identifier; contact meshes are not
joined. A region can therefore be selected either in the viewport or in the
Interactions tree. The **Show** column controls one region, all regions on an
element-pair edge, or the complete contact layer through the **All
interactions** row. Viewport selection is synchronized back to the tree and
selection inspector when COMPAS Viewer refreshes its sidebar.

This region-level representation intentionally trades a larger scene-object
count for independently verifiable picking and visibility. Applications that
only need the model geometry can construct `ModelViewer(...,
show_contacts=False)`; the contact objects still exist for inspection but
start hidden.

An optional `selection_changed` callback receives the selected elements and is
the intended integration point for the element properties and attributes
inspector. Applications that provide a different UI can construct
`ModelViewer(..., install_tree=False)` and use the controller lookup and
selection APIs directly.

### Selection inspector

`ElementInspector` adds a read-only `Selection` tab to the COMPAS Viewer
sidebar. Despite its compatibility-preserving class name, it displays both
element and contact selections. For a contact selection it reports the two
incident elements, selected region count, total area, and each region's area,
boundary-point count, hole count, and triangulated face count.

For a single selected element it reports:

- identity, parent, child count, selection, and visibility;
- element parameters exposed through serialized `Element.__data__`, excluding
  infrastructure fields such as transformation, features, and material links;
- semantic attributes stored on the element's model-tree node;
- assigned material type, GUID, and serialized properties;
- source Mesh or BRep topology counts, geometry revision, and generated render
  buffer counts.

For multiple elements the inspector reports the selection count, type
distribution, and visible count. `inspect_elements` produces the same
structured `InspectorSection` data independently of the Qt widget, making the
display logic directly testable and reusable by other interfaces.

The inspector deliberately starts read-only. Editing arbitrary serialized
values would bypass element validation and geometry invalidation; editable
controls should therefore be added later through explicit parameter metadata
and setters rather than generic attribute assignment. Applications can disable
automatic installation with `ModelViewer(..., install_inspector=False)`.

## Cross-vault example

`examples/contact_detection/cross_vault_model_viewer.py` demonstrates the
complete infrastructure with the 184-block cross vault. It computes the block
contacts, organizes blocks into four overlapping-capable spatial collections,
exposes contact
counts as tree-node attributes, preselects the block with the most contact
regions, and displays every contact interface as an independently selectable
red region.

```bash
python examples/contact_detection/cross_vault_model_viewer.py
```

Use the collection checkboxes to hide an entire quadrant, compare the
hierarchy, collection, and type projections, select contact pairs or regions in the
Interactions tab, and inspect their computed geometry in the Selection tab.
The computational setup can be verified without opening a window:

```bash
python examples/contact_detection/cross_vault_model_viewer.py --no-viewer
```

## Revisions, caching, and identity

### Units and approximation quality

`Model.unit` records whether coordinate values are metres (`M`) or millimetres
(`MM`). It is serialized with the model. Changing the metadata reinterprets
coordinate values; it never scales existing geometry.

`RenderSettings` derives linear deflection from the diagonal of each element's
axis-aligned bounding box and then clamps it to physical limits converted into
model units:

```text
linear deflection = clamp(relative deflection × diagonal,
                          physical minimum,
                          physical maximum)
```

| Quality | Relative deflection | Physical minimum | Physical maximum | Angular deflection |
| --- | ---: | ---: | ---: | ---: |
| `draft` | `1e-2 × diagonal` | 0.1 mm | 20 mm | 0.20 rad |
| `standard` | `1e-3 × diagonal` | 0.01 mm | 5 mm | 0.10 rad |
| `high` | `1e-4 × diagonal` | 0.001 mm | 1 mm | 0.05 rad |

For example, a one-metre object at standard quality uses a one-millimetre
deflection: `0.001` in a metre model or `1.0` in a millimetre model. A
ten-metre object uses the five-millimetre physical maximum rather than an
unbounded relative error. Degenerate and extremely small objects use the
physical minimum. Translation does not affect the diagonal, so large global
coordinates do not coarsen tessellation; algorithms operating far from the
origin may nevertheless require local-coordinate conditioning for numerical
robustness.

Angular deflection is unitless. The default Mesh cleanup tolerance is separate
from visual tessellation and represents the same physical distance: `1e-9`
metres or `1e-6` millimetres. Explicit tolerance and deflection values are
interpreted in model units and override the presets.

An `ElementObject` with implicit settings adopts its model's unit and tracks
later metadata changes when its render geometry is refreshed. Explicit
settings must use the same unit as the model, preventing an accidental
metre/millimetre mismatch.

Every element has a runtime-only `geometry_revision`. Existing element and
model invalidation paths increment this revision whenever they clear derived
geometry. The revision is deliberately not serialized: deserialized elements
start a new runtime cache lifecycle.

`RenderGeometryCache` keys entries by element GUID and verifies all of the
following before returning a hit:

- the Python element identity is unchanged;
- `geometry_revision` is unchanged;
- Mesh triangulation and BRep tessellation settings are unchanged.

This prevents a different element carrying the same GUID, stale derived
geometry, or a different tessellation quality from reusing an incompatible
render snapshot. `ElementObject` owns the resulting snapshot directly; there
is no separate element-view state or duplicated render-geometry reference.
Explicit invalidation is also available. Direct in-place
mutation of the Mesh or BRep stored inside an element cannot be observed by the
element setter and therefore requires explicit cache invalidation; assigning
the geometry property or using model/element transformations updates the
revision automatically.

The current model invalidation policy is deliberately conservative: a geometry
change can affect descendants, interactions, and modifiers, so it increments
the revisions of all elements in the model. The cache still avoids rebuilding
anything until a view is refreshed, but a complete model refresh may rebuild
all element render geometry after such a change. More selective dependency
tracking can be added later without changing the cache contract. A future
model-viewer controller can index the concrete element objects by GUID for tree
selection and visibility control without introducing another state owner.

## Ear-clipping methodology

`triangulate_polygon_earcut` provides reusable triangulation for a planar
exterior ring with optional holes. It performs the following steps:

1. Remove a repeated closing point, consecutive duplicates, and collinear
   points within the requested tolerance.
2. Compute the exterior Newell normal and project all rings by dropping its
   dominant coordinate.
3. Reject degenerate or topologically invalid projected polygons with Shapely.
4. Triangulate the projected rings with Mapbox Earcut.
5. Restore the exterior ring's original winding to the generated triangles.
6. Compare the summed triangle area with the validated polygon area and reject
   incomplete output.

Earcut is designed to return useful results for practical polygon data and is
not a formal guarantee for arbitrary invalid or self-intersecting input. The
explicit validity and area checks prevent such output from silently entering
render buffers. Projection assumes that input rings describe one planar face;
it does not repair materially nonplanar faces.

## Verification

The numerical triangulation and render-buffer topology can be checked without
starting a graphical interface:

```bash
pytest tests/test_geometry_triangulation.py
pytest tests/test_viewer_rendergeometry.py
pytest tests/test_viewer_viewstate.py
pytest tests/test_viewer_controller.py
pytest tests/test_viewer_treeform.py
```

The tests cover concavity, winding, holes, duplicate and collinear vertices,
degenerate and self-intersecting input, invalid indices, hidden triangulation
diagonals, native OCC view-mesh boundaries, model hierarchy mapping, selection,
visibility, cache reuse, refresh, units, and empty models.

