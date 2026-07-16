# -*- coding: utf-8 -*-

"""
Helpers for the Pipeline Batcher UI
"""

# ========== Py standard lib imports ==========
import re
import glob
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


class PathTemplate:
    """
    Simple Path Template generation helper
    It is built from a template string : `{root}/test/path/{fieldNameA}/{fieldNameB}-v{version}.ext`
    And provide the following functions:
    - `list_files`: list all versions of a file matching the template and required fields.
    - `getNextPath`: get the file path for the next version.
    """

    def __init__(self, template: str):
        self.template = template
        self.fields = re.findall(r'\{(\w+)\}', template)

    def checkFields(self, data: dict):
        missing = [f for f in self.fields if f != 'version' and f not in data]
        if missing:
            raise ValueError(f"Missing fields: {missing}")

    def applyFields(self, data: dict, versionWildcard: str = None) -> str:
        """ Generate a path from the template and fields.
        A wildcard or specific pattern can be used for the version field.
        """
        path = self.template
        for field in self.fields:
            if field == 'version':
                version = versionWildcard if versionWildcard else data.get('version', '{version}')
                path = path.replace('{version}', version)
            else:
                path = path.replace(f'{{{field}}}', str(data[field]))
        return path

    def listFiles(self, data: dict) -> list[str]:
        """ List all files corresponding to the template and given fields. """
        self.checkFields(data)
        pattern = self.applyFields(data, versionWildcard='*')
        return sorted(glob.glob(pattern))
    
    def getExistingVersions(self, data: dict) -> list[int]:
        """ Get existing versions on disk for the template and given fields. """
        self.checkFields(data)
        existing = self.listFiles(data)
        if not existing:
            return []

        # Extract version numbers from existing files
        versionPattern = self.applyFields(data, versionWildcard=r'(\d+)')
        versions = [
            int(m.group(1))
            for f in existing
            if (m := re.search(versionPattern, f))
        ]
        return versions

    def getNextPath(self, data: dict) -> str:
        """ Get the path with an incremented version from what we already have on disk. """
        self.checkFields(data)
        versions = self.getExistingVersions(data)
        vup = max(versions) + 1 if versions else 1
        return self.applyFields({**data, 'version': str(vup).zfill(3)})
