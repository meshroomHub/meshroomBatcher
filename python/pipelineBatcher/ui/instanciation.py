"""
Helpers for the Pipeline Batcher UI
"""

# ========== Py standard lib imports ==========
from pathlib import Path
import logging
import json
from typing import Any, TYPE_CHECKING
from dataclasses import dataclass, field
from collections import namedtuple
from enum import Enum

# ========== External libraries ==========
from PySide6.QtCore import (
    Qt,
    QAbstractListModel,
    QModelIndex,
    QObject,
    Slot,
    Signal,
    Property
)

# ========== Meshroom imports ==========
from meshroom.core.node import Position
from meshroom.core.graph import Graph

if TYPE_CHECKING:
    from meshroom.ui.app import MeshroomApp
    from meshroom.ui.graph import UIGraph

# ========== Imports from current package ==========
from pipelineBatcher.utilities import parseNodeParam
from pipelineBatcher.entityProvider import EntityBase, TemplateInfo, EntityProviderRegistry, EntityCache


OverrideParameter = namedtuple("OverrideParameter", ("node_instance", "parameter_name", "value"))


class InstancingMode(Enum):
    LIVE_SCENE   = 0
    UNIQUE_FILES = 1


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


class CreatedFilesModel(QAbstractListModel):
    NameRole = Qt.UserRole + 1
    PathRole = Qt.UserRole + 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list[tuple[str, str]] = []

    def add(self, name: str, path: str):
        self.beginInsertRows(QModelIndex(), len(self._items), len(self._items))
        self._items.append((name, path))
        self.endInsertRows()

    def rowCount(self, parent=QModelIndex()):
        return len(self._items)

    def data(self, index, role):
        if not index.isValid():
            return None
        name, path = self._items[index.row()]
        if role == self.NameRole:
            return name
        if role == self.PathRole:
            return path
        return None

    def roleNames(self):
        return {self.NameRole: b"entityName", self.PathRole: b"filePath"}


class TemplateInstanciator(QObject):
    """ Creates Meshroom nodes for one entity at a time. """

    def __init__(self, app, state: TemplateCreationState, parent=None):
        """
        Args:
            app         : MeshroomApp instance (has .graph property).
            tplPath     : Absolute path to the .mg template file.
            entityParams: {sg_field: "NodeInstance:paramName"} for the entity input.
            parameters  : {"NodeInstance:paramName": value, ...} for extra params.
            entities    : list of entities
        """
        super().__init__(parent)

        self._selectedTemplate: TemplateInfo = state.selected_template
        templateIndex = self._selectedTemplate.index
        self._templateName = self._selectedTemplate.getName()
        templatePath = self._selectedTemplate.template
        entityParams = self._selectedTemplate.input_entity_params
        entities     = [EntityCache.get(templateIndex, eId) for eId in state.selected_entities]

        self._app: "MeshroomApp" = app
        try:
            self._uigraph: "UIGraph" = app._activeProject  # UIGraph (Scene)
            self._instancingMode = InstancingMode.LIVE_SCENE
        except Exception:
            self._uigraph = None
            self._instancingMode = InstancingMode.UNIQUE_FILES
        self._parameters = [OverrideParameter(*k.split(":"), v) for k, v in state.parameters.items()]
        self._entities: list[EntityBase] = entities
        self._tplPath = templatePath
        self._provider = EntityProviderRegistry.getProviderFromTemplate(templateIndex)

        logging.debug("TemplateInstanciator")
        logging.debug("  templatePath:", templatePath)
        logging.debug("  entityParams:", entityParams)
        logging.debug("  parameters  :", self._parameters)
        logging.debug("  entities    :", entities    )

        self._entityParams: list[tuple[str, str, str]] = []  # node_instance, param_name, sg_field
        for sgField, entityParam in entityParams.items():
            self._entityParams.append((*parseNodeParam(entityParam), sgField))

        # Pre-compute template origin
        self._tplGraphData = self._loadTemplate(templatePath)
        nodes = self._tplGraphData.get("graph", {})
        all_pos = [v.get("position", [0, 0]) for v in nodes.values()]
        self.x0 = min(p[0] for p in all_pos) if all_pos else 0
        self.y0 = min(p[1] for p in all_pos) if all_pos else 0
        
        # Store unique files for the final page
        self._createdFiles = CreatedFilesModel(parent=self)
    
    def getMode(self):
        return self._instancingMode.name

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
        """Create the instance and return a list of nodes."""
        if entityIndex >= len(self._entities):
            logging.error(f"Entity index {entityIndex} out of range.")
            return []

        entity = self._entities[entityIndex]        
        g = Graph("")
        g._deserialize(Graph._loadGraphData(self._tplPath))

        # Update graph
        for node in g.nodes:
            # Set position
            node.position = Position(node.x - self.x0, node.y - self.y0 + yOffset)
            # Set entity override
            for node_inst, param_name, sg_field in self._entityParams:
                if node_inst == node.name and node.hasAttribute(param_name):
                    node.attribute(param_name).value = getattr(entity, sg_field, "")
            # Set parameter override
            for override in self._parameters:
                if override.node_instance == node.name and node.hasAttribute(override.parameter_name):
                    node.attribute(override.parameter_name).value = override.value

        # Apply the graph
        if self._instancingMode == InstancingMode.LIVE_SCENE:
            # Update the entity on the graph
            self._provider.updateEntityOnGraph(self._selectedTemplate, g, entity)
            # Import on current graph
            return self._uigraph._graph.importGraphContent(g)
        else:
            self._createInstanceOnUniqueScene(g, entity)
            return list(g.nodes)

    def _createInstanceOnUniqueScene(self, graph: Graph, entity: EntityBase):
        logging.info(f"(_createInstanceOnUniqueScene) entity: {entity}")
        # Update the entity on the graph
        self._provider.updateEntityOnGraph(self._selectedTemplate, graph, entity)
        filePath = self._provider.generateScenePath(self._templateName, entity)
        # Generate scene
        Path(filePath).parent.mkdir(parents=True, exist_ok=True)
        logging.info(f"Save scene to {filePath}")
        graph.save(filePath)
        self._createdFiles.add(entity.entity_name, filePath)

    @Slot(QObject, str)
    def setBackdropName(self, backdropNode, label: str):
        """
        Set the label and comment on a backdrop node.
        Needed because node.internalAttribute() has no @Slot and can't be called from QML.
        """
        if self._instancingMode != InstancingMode.LIVE_SCENE:
            return
        if backdropNode and backdropNode.hasInternalAttribute("label"):
            self._uigraph.setAttribute(backdropNode.internalAttribute("label"), label)
            self._uigraph.setAttribute(backdropNode.internalAttribute("comment"), label)

    done = Signal()
    errorOccurred = Signal(str)
    mode = Property(str, getMode, constant=True)
    createdFiles = Property(QObject, lambda self: self._createdFiles, constant=True)
