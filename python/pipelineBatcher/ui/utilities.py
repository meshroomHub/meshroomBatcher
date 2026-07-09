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
from meshroom.core.node import Position

if TYPE_CHECKING:
    from meshroom.ui.app import MeshroomApp
    from meshroom.ui.graph import UIGraph

# ========== Imports from current package ==========
from pipelineBatcher.ui.entities import get_entity, CachedEntity


OverrideParameter = namedtuple("OverrideParameter", ("node_instance", "parameter_name", "value"))


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
    selected_template: dict | None = None
    selected_entities: list[str] = field(default_factory=list)
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
            and self.selected_template.get("parameters")
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
        self._entities: list[CachedEntity]   = entities

        self._entityParams: list[tuple[str, str, str]] = []  # node_instance, param_name, sg_field
        for sgField, entityParam in entityParams.items():
            self._entityParams.append((*parseNodeParam(entityParam), sgField))

        # Pre-compute template origin
        nodes = self._loadTemplate(tplPath).get("graph", {})
        all_pos = [v.get("position", [0, 0]) for v in nodes.values()]
        self.x0 = min(p[0] for p in all_pos) if all_pos else 0
        self.y0 = min(p[1] for p in all_pos) if all_pos else 0
        self._nodes_tpl  = nodes
    
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
    def createInstanceForEntity(self, entityIndex: int, offset: int) -> list:
        """Creates all nodes for entities[entityIndex] at the given Y offset.
        
        Args:
            entityIndex : index into self._entities
            offset      : offset to apply to the Y position to avoid overlap

        Returns:
            List of created node names
        """
        if entityIndex >= len(self._entities):
            logging.error(f"Entity index {entityIndex} out of range.")
            return []

        entity   = self._entities[entityIndex]
        created  = []

        for tpl_node_name, node_data in self._nodes_tpl.items():
            node_type = node_data.get("nodeType", tpl_node_name)
            pos       = node_data.get("position", [0, 0])
            x = pos[0] - self.x0
            y = pos[1] - self.y0 + offset

            node = self._uigraph.addNewNode(node_type, Position(x, y))
            created.append(node)

            # Entity-driven inputs
            for (node_inst, param_name, sg_field) in self._entityParams:
                if node_inst == tpl_node_name:
                    node.attribute(param_name).value = getattr(entity, sg_field, "")

            # Parameter overrides
            for override in self._parameters:
                if override.node_instance == tpl_node_name:
                    node.attribute(override.parameter_name).value = override.value

        return created

    @Slot(QObject, str)
    def setBackdropLabel(self, backdropNode, label: str):
        """
        Set the label on a backdrop node.
        Needed because node.internalAttribute() has no @Slot and can't be called from QML.
        """
        if backdropNode and backdropNode.hasInternalAttribute("label"):
            self._uigraph.setAttribute(backdropNode.internalAttribute("label"), label)
    
    done = Signal()
    errorOccurred = Signal(str)


def build_instanciator(app, state: TemplateCreationState) -> TemplateInstanciator:
    template     = state.selected_template["template"]
    entityParams = state.selected_template.get("input_entity_params", {})
    entities     = [get_entity(eid) for eid in state.selected_entities]
    parameters   = [OverrideParameter(*k.split(":"), v) for k, v in state.parameters.items()]
    return TemplateInstanciator(app, template, entityParams, parameters, entities)
