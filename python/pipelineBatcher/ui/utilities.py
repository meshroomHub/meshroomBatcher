"""
Helpers for the Pipeline Batcher UI
"""

# ========== Py standard lib imports ==========
import logging
import json
from typing import Any, TYPE_CHECKING
from dataclasses import dataclass, field
from collections import namedtuple

# ========== External libraries ==========
from PySide6.QtCore import QObject, Slot, Signal

# ========== Meshroom imports ==========
from meshroom.core import pluginManager
from meshroom.core.node import Position
from meshroom.core.graph import Graph

if TYPE_CHECKING:
    from meshroom.ui.app import MeshroomApp
    from meshroom.ui.graph import UIGraph

# ========== Imports from current package ==========
from pipelineBatcher.ui.entityProvider import EntityBase, EntityCache, TemplateInfo


OverrideParameter = namedtuple("OverrideParameter", ("node_instance", "parameter_name", "value"))


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


@dataclass
class TemplateCreationState:
    entity_type: str = ""
    selected_template: TemplateInfo | None = None
    selected_entities: list[str] = field(default_factory=list)
    """list of IDs of selected entities"""
    parameters: dict[str, Any] = field(default_factory=dict)

    def reset(self):
        self.entity_type = ""
        self.selected_template = None
        self.selected_entities.clear()
        self.parameters.clear()

    @property
    def needs_parameter_page(self) -> bool:
        return bool(
            self.selected_template
            and len(self.selected_template.parameters) > 0
        )


class TemplateInstanciator(QObject):
    """ Creates Meshroom nodes for one entity at a time. """

    def __init__(self, app, tplPath, entityParams, parameters, entities, parent=None):
        """
        Args:
            app         : MeshroomApp instance (has .graph property).
            tplPath     : Absolute path to the .mg template file.
            entityParams: {sg_field: "NodeInstance:paramName"} for the entity input.
            parameters  : {"NodeInstance:paramName": value, ...} for extra params.
            entities    : list of entities
        """
        super().__init__(parent)
        self._app: "MeshroomApp" = app
        self._uigraph: "UIGraph" = app._activeProject  # UIGraph (Scene)
        self._parameters: list[OverrideParameter] = parameters
        self._entities: list[EntityBase] = entities
        self._tplPath = tplPath

        logging.debug("TemplateInstanciator")
        logging.debug("  tplPath     :",      tplPath)
        logging.debug("  entityParams:", entityParams)
        logging.debug("  parameters  :", parameters  )
        logging.debug("  entities    :", entities    )

        self._entityParams: list[tuple[str, str, str]] = []  # node_instance, param_name, sg_field
        for sgField, entityParam in entityParams.items():
            self._entityParams.append((*parseNodeParam(entityParam), sgField))

        # Pre-compute template origin
        self._tplGraphData = self._loadTemplate(tplPath)
        nodes = self._tplGraphData.get("graph", {})
        all_pos = [v.get("position", [0, 0]) for v in nodes.values()]
        self.x0 = min(p[0] for p in all_pos) if all_pos else 0
        self.y0 = min(p[1] for p in all_pos) if all_pos else 0

    @property
    def graph(self) -> Graph:
        return self._uigraph._graph

    @staticmethod
    def _loadTemplate(tplPath: str) -> dict:
        try:
            with open(tplPath, "r") as f:
                return json.load(f)
        except Exception as exc:
            logging.error(f"Cannot load template '{tplPath}': {exc}")
            return {}

    @Slot(result=int)
    def entityCount(self):
        return len(self._entities)
    
    @Slot(int, result=str)
    def entityName(self, index):
        """Return name for entity at index."""
        if 0 <= index < len(self._entities):
            return self._entities[index].entity_name
        return ""

    @Slot(int, result=str)
    def entityLabel(self, index):
        """Return the display name for entity at index (used for backdrop label)."""
        if 0 <= index < len(self._entities):
            return self._entities[index].entity_name
        return ""

    @Slot(int, int, result="QVariantList")
    def createInstanceForEntity(self, entityIndex: int, yOffset: int) -> list:
        if entityIndex >= len(self._entities):
            logging.error(f"Entity index {entityIndex} out of range.")
            return []

        entity     = self._entities[entityIndex]
        live_graph = self._uigraph._graph

        tmp_graph = Graph("")
        tmp_graph._deserialize(Graph._loadGraphData(self._tplPath))
        
        for node in tmp_graph.nodes:
            node.position = Position(node.x - self.x0, node.y - self.y0 + yOffset)

            for node_inst, param_name, sg_field in self._entityParams:
                if node_inst == node.name and node.hasAttribute(param_name):
                    node.attribute(param_name).value = getattr(entity, sg_field, "")

            for override in self._parameters:
                if override.node_instance == node.name and node.hasAttribute(override.parameter_name):
                    node.attribute(override.parameter_name).value = override.value

        return live_graph.importGraphContent(tmp_graph)

    @Slot(QObject, str)
    def setBackdropName(self, backdropNode, label: str):
        """
        Set the label and comment on a backdrop node.
        Needed because node.internalAttribute() has no @Slot and can't be called from QML.
        """
        if backdropNode and backdropNode.hasInternalAttribute("label"):
            self._uigraph.setAttribute(backdropNode.internalAttribute("label"), label)
            self._uigraph.setAttribute(backdropNode.internalAttribute("comment"), label)
    
    done = Signal()
    errorOccurred = Signal(str)


def build_instanciator(app, state: TemplateCreationState) -> TemplateInstanciator:
    templateIndex = state.selected_template.index
    templatePath = state.selected_template.template
    entityParams = state.selected_template.input_entity_params
    entities     = [EntityCache.get(templateIndex, eId) for eId in state.selected_entities]
    parameters   = [OverrideParameter(*k.split(":"), v) for k, v in state.parameters.items()]
    return TemplateInstanciator(app, templatePath, entityParams, parameters, entities)
