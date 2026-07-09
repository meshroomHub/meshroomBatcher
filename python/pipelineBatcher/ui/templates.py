"""
Templates Helper for the Pipeline Batcher UI
"""

# ========== Py standard lib imports ==========
import json
import logging
import os
from pathlib import Path

# ========== External libraries ==========

# ========== Meshroom imports ==========
from meshroom.core import nodeFactory, desc
from meshroom.core import pluginManager

# ========== Imports from current package ==========


MR_TYPE_MAP = {
    "StringParam": "string",
    "File": "file",
    "IntParam": "int",
    "FloatParam": "float",
    "BoolParam": "bool",
    "ChoiceParam": "choice",
    "ColorParam": "string",
}


def get_templates_dir() -> str:
    """ Get the folder with the templates inside
    """
    resources = os.getenv("PIPELINE_RESOURCES")
    templatesFolder = Path(resources) / "batchPipelines"
    return str(templatesFolder)


def remap_template_path(path: str) -> str:
    """ Used to replace env vars inside the path
    """
    env = {
        "RESOURCES": os.getenv("PIPELINE_RESOURCES")
    }
    for k, v in env.items():
        to_sub = "{" + k + "}"
        if to_sub in path:
            path = path.replace(to_sub, v)
    return path


def list_templates(templatesFolder: str) -> list[dict]:
    """
    Scan templates_dir for JSON files and return a list with the detected templates.
    """
    results = []
    if not os.path.isdir(templatesFolder):
        logging.warning(f"Templates directory does not exist: {templatesFolder}")
        return results

    for tplName in sorted(os.listdir(templatesFolder)):
        if not tplName.endswith(".json"):
            continue
        tplPath = os.path.join(templatesFolder, tplName)
        try:
            with open(tplPath, "r") as f:
                data = json.load(f)
            data.setdefault("name", os.path.splitext(tplName)[0])
            data.setdefault("description", "")
            data.setdefault("parameters", [])
        except Exception as exc:
            logging.warning(f"Could not parse template '{tplPath}': {exc}")
        else:
            requiredKeys = ("template", "input_entity_type", "input_entity_params")
            missingKeys = set()
            for k in requiredKeys:
                if k not in data.keys():
                    missingKeys.add(k)
            if missingKeys:
                logging.warning(f"Template {tplPath} have missing info : {list(missingKeys)}")
            else:
                data["template"] = remap_template_path(data["template"])
                results.append(data)

    logging.info(f"Found {len(results)} template(s) in '{templatesFolder}'")
    return results


def buildTemplatesIndex(templatesFolder):
    templatesIndex = {}
    templates = list_templates(templatesFolder)
    for i, tpl in enumerate(templates):
        tpl["index"] = i
        templatesIndex[i] = tpl
    return templatesIndex


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
    
    try:
        with open(path, "r") as f:
            mg = json.load(f)

        nodes = mg.get("graph", {})
        if nodeInstance not in nodes:
            logging.warning(
                f"Node '{nodeInstance}' not found in '{path}'. "
                f"Available: {list(nodes.keys())}"
            )
            return None

        node_data = nodes[nodeInstance]
        node_type = node_data.get("nodeType", "")

        # Try to resolve the node descriptor from Meshroom's registry
        try:
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
        except Exception as inner:
            logging.debug(f"Descriptor lookup failed: {inner}")

        return None

    except Exception as exc:
        logging.warning(
            f"get_param_info failed for "
            f"'{nodeInstance}:{paramName}' in '{path}': {exc}"
        )
        return None
