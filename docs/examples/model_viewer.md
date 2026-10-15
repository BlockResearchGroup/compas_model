# Model Viewer Example

The cross-vault viewer demonstrates the reusable viewer infrastructure with a
nontrivial model:

```bash
python examples/contact_detection/cross_vault_model_viewer.py
```

It loads the original polygonal block meshes, computes contacts, and provides
navigation by hierarchy, collection, element type, and interaction. Contacts
are individual selectable scene objects and can be hidden independently.

Install the viewer extra first:

```bash
python -m pip install -e ".[viz]"
```

Use `--no-viewer` to build and verify the model without launching the GUI.
