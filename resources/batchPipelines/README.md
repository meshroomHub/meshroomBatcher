# Pipelines

Expected JSON schema per file:
```json
{
    "name":               "My Pipeline",         // optional, defaults to filename
    "description":        "...",                 // optional
    "template":           "path/to/file.mg",     // path to the .mg file
    "input_entity_type":  "Asset",               // Shotgrid entity (Sequence, Asset, Shot, Version, etc)
    "input_entity_params": {                     // Parameter where on the template we can set the entity info
        "asset_name": "NodeInstance:paramName",
        "asset_type": "NodeInstance:paramName",
    },
    "parameters": [                              // Additional parameters to fill. They will require User inputs
        "NodeInstance:paramName",
        ...
    ]
}
```
