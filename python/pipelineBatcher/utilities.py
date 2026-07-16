"""
Helpers for the Pipeline Batcher UI
"""

# ========== Py standard lib imports ==========
import json
from pathlib import Path
from collections import namedtuple

# ========== Meshroom imports ==========
from meshroom.core import pluginManager


OverrideParameter = namedtuple("OverrideParameter", ("node_instance", "parameter_name", "value"))


def import_provider(modulePath: str):
    import sys
    import importlib.util
    moduleName = "mockEntityProvider"
    moduleName = Path(modulePath).stem
    spec = importlib.util.spec_from_file_location(moduleName, str(modulePath))
    foo = importlib.util.module_from_spec(spec)
    sys.modules[moduleName] = foo
    spec.loader.exec_module(foo)


MR_TYPE_MAP = {
    "StringParam": "string",
    "File": "file",
    "IntParam": "int",
    "FloatParam": "float",
    "BoolParam": "bool",
    "ChoiceParam": "choice",
    "ColorParam": "string",
}


def getMgParameterInfo(path: str, nodeInstance: str, paramName: str) -> dict:
    """Introspect a Meshroom .mg file to determine the type of a parameter.

    Args:
        path:         Absolute path to the .mg template file.
        nodeInstance: Node name as it appears in the graph (e.g. "CameraInit_1").
        paramName:    Attribute name on that node (e.g. "viewpoints").

    Returns a dict:
        - type: "string" | "int" | "float" | "bool" | "choice" | "file",
        - node: node instance name
        - paramName: parameter name
        - default: default value or None
        - choices: for choice widget : all possible choices
    """
    with open(path, "r") as f:
        mg = json.load(f)

    nodes = mg.get("graph", {})
    if nodeInstance not in nodes:
        raise ValueError(
            f"Node '{nodeInstance}' not found in '{path}'. "
            f"Available: {list(nodes.keys())}"
        )

    node_data = nodes[nodeInstance]
    node_type = node_data.get("nodeType", "")

    # g = Graph("").load(template)
    # g._nodes["GraphInput"].getAttributes()
    nodeDescClass = pluginManager.getRegisteredNodePlugin(node_type).nodeDescriptor
    if nodeDescClass is None:
        return None

    nodeDesc = nodeDescClass()
    for attrDesc in nodeDesc.inputs:
        if attrDesc.name == paramName:
            type_name = type(attrDesc).__name__
            mapped = MR_TYPE_MAP.get(type_name, "string")
            result = {
                "type": mapped,
                "node": nodeInstance,
                "paramName": paramName,
                "default": attrDesc.value if hasattr(attrDesc, "value") else None,
                "choices": [],
            }
            if mapped == "choice" and hasattr(attrDesc, "values"):
                result["choices"] = list(attrDesc.values)
            return result

    return None


def parseNodeParam(nodeParam: str):
    """ Split "NodeInstance:paramName" into ("NodeInstance", "paramName").
    """
    parts = nodeParam.split(":", 1)
    if len(parts) != 2:
        raise ValueError(f"Expected 'NodeInstance:paramName', got '{nodeParam}'")
    return (parts[0].strip(), parts[1].strip())
