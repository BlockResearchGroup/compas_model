# Examples

The repository examples are executable checks as well as visual demonstrations.
Most accept `--no-viewer` so their assertions can run on a headless machine.

- [Collision detection](collision_detection.md) compares conservative and
  precise Mesh and BRep checks.
- [Contact detection](contact_detection.md) displays computed interface
  regions, including disconnected regions and holes.
- [Sections and clips](sectioning.md) compares section-only output with
  retained half-space geometry.
- [Model viewer](model_viewer.md) loads the cross vault and exposes model
  hierarchy, collections, element types, interactions, and individual
  contacts.

Run scripts from the repository root so their shared helpers and data paths
resolve consistently.
