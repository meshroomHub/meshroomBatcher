"""
Entities Helper for the Pipeline Batcher UI
"""

# ========== Py standard lib imports ==========
import logging
import inspect
from pathlib import Path
from types import SimpleNamespace
from collections import defaultdict
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field

from pipelineBatcher.ui.utilities import parseNodeParam

from meshroom.core.graph import Graph
from meshroom.core.node import Position


class EntityBase(SimpleNamespace):
    def __init__(self, entity_type, entity_name, **kwargs):
        super().__init__(**kwargs)
        self.entity_type = entity_type
        self.entity_name = entity_name
        if "id" not in kwargs:
            self.id = f"{entity_type.lower()}.{entity_name}"

    def __contains__(self, item):
        return item in self.__dict__

    def toDict(self):
        return {
            "id": self.id,
            "name": self.entity_name,
            "status": self.status if "status" in self else "",
            "description": self.description if "description" in self else ""
        }


class EntityCache:
    _cache = defaultdict(dict)  # {templateIndex: {entityId: CachedEntity}}

    @classmethod
    def add(cls, templateIndex: int, entity: EntityBase):
        cls._cache[templateIndex][entity.id] = entity

    @classmethod
    def get(cls, templateIndex: int, entityId: str) -> EntityBase:
        return cls._cache.get(templateIndex, {}).get(entityId, None)

    @classmethod
    def contains(cls, templateIndex: int, entityId: str) -> bool:
        if templateIndex not in cls._cache:
            return False
        return entityId in cls._cache[templateIndex]


def get_entity(entity_id: str) -> EntityBase:
    return EntityCache.get(entity_id)


@dataclass
class TemplateInfo:
    # Path to the template file
    template: str
    # Name of the entity corresponding that applies to the template
    input_entity_type: str
    # The corresponding parameter in the graph that corresponds to the input entity
    #   {"entity_name": "Code_1:string"} means the `entity_name` field of the entity
    #   (from the CachedEntity) will be set to the attribute `string` of the node `Code_1`.
    input_entity_params: dict[str, str]

    # --- Optional attributes ---
    # Name of the template
    name: str = ""
    # Description of the template
    description: str = ""
    # Optional list of parameters exposed to the users
    #   ["InputInt_1:param"] means the attribute `param` of the node `InputInt_1` will be exposed.
    #   TODO: Remplace with the `GraphInput` feature
    parameters: list[str] = field(default_factory=lambda: [])
    # Global index. Set by the EntityProviderRegistry.
    index: int = -1

    def getName(self):
        return self.name or Path(self.template).stem

    @classmethod
    def fromDict(cls, data: dict):
        REQUIRED_KEYS = ("template", "input_entity_type", "input_entity_params")
        missingKeys = [k for k in REQUIRED_KEYS if k not in data]
        if missingKeys:
            logging.warning(f"Missing keys ({', '.join(missingKeys)}) in template:\n{data}")
            return None
        data = {k:v for k, v in data.items() if k in cls.__dataclass_fields__.keys()}
        return cls(**data)

    def toDict(self):
        tplDict = {**asdict(self), "name": self.getName()}
        return tplDict


class EntityProvider(ABC):
    """Base class for entity providers."""

    name: str = ""

    @classmethod
    def getName(cls):
        if cls.name:
            return cls.name
        return cls.__name__
    
    @classmethod
    def getModulePath(cls):
        return inspect.getfile(cls)

    def __repr__(self):
        return f"<EntityProvider {self.getName()} at {self.getModulePath()}>"

    @abstractmethod
    def listAvailableTemplates(self) -> list[TemplateInfo]:
        """List templates provided by this provider
        """
        raise NotImplementedError()

    @abstractmethod
    def getEntitiesTree(self, templateName: str) -> list[dict]:
        """Return the navigation tree for entity_type.

        Keys:
        - id      : stable identifier used in fetchEntitiesByGroup
        - label   : human-readable display name
        - icon    : optional emoji / single unicode character
        - children: child items
        """
        raise NotImplementedError()

    @abstractmethod
    def fetchEntitiesByGroup(self, templateName: str, group_id: str) -> list[EntityBase]:
        """Return entities belonging to group_id for the given entity_type.

        Keys:
        - id         : passed back to the pipeline as the entity value
        - name       : displayed in the Name column
        - status     : displayed as a coloured badge (optional)
        - description: displayed in the Description column (optional)
        """
        raise NotImplementedError()

    @staticmethod
    def updateEntityOnGraph(template: TemplateInfo, graph: Graph, entity: EntityBase):
        # Build the dict node_instance -> (attribute, entity_field)
        entityParams: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for field, entityParam in template.input_entity_params.items():
            nodeInstance, paramName = parseNodeParam(entityParam)
            entityParams[nodeInstance].append((paramName, field))
        # Apply fields on graph
        for node in graph.nodes:
            for paramName, field in entityParams.get(node.name, []):
                if node.hasAttribute(paramName):
                    node.attribute(paramName).value = getattr(entity, field, "")

    @abstractmethod
    def generateScenePath(self, templateName: str, entity: EntityBase):
        raise NotImplementedError()


class EntityProviderRegistry(object):
    _registry: dict[str, EntityProvider] = dict()
    """provider name to provider object"""
    _templates: dict[int, TemplateInfo] = dict()
    """template index to template dict"""
    _templateProvider: dict[int, str] = dict()
    """template index to provider name"""

    @classmethod
    def register(cls, provider: EntityProvider):
        name = provider.getName()
        logging.info(f"Registering provider {provider}")
        cls._registry[name] = provider
        # Register all templates from this provider
        for provider in cls.listEntityProviders():
            providerTemplates = provider.listAvailableTemplates()
            for tpl in providerTemplates:
                if not isinstance(tpl, TemplateInfo):
                    logging.warning(f"Cannot register template {tpl}: not a TemplateInfo.")
                    continue
                tplIndex = len(cls._templateProvider)
                tpl.index = tplIndex
                cls._templates[tplIndex] = tpl
                cls._templateProvider[tplIndex] = provider.getName()

    @classmethod
    def getEntityProvider(cls, name) -> EntityProvider:
        return cls._registry.get(name)

    @classmethod
    def listEntityProviders(cls) -> list[EntityProvider]:
        return list(cls._registry.values())

    @classmethod
    def getTemplateIndex(cls) -> dict[int, TemplateInfo]:
        return cls._templates

    @classmethod
    def getTemplateName(cls, templateIndex: int) -> str:
        if templateIndex not in cls._templateProvider:
            return "unknown"
        return cls._templates[templateIndex].getName()
    
    @classmethod
    def getProviderFromTemplate(cls, templateIndex: int) -> EntityProvider:
        if templateIndex not in cls._templateProvider:
            raise KeyError(f"No provider for template {templateIndex}")
        providerName = cls._templateProvider[templateIndex]
        return cls._registry[providerName]

    @classmethod
    def listTemplates(cls):
        return list(cls._templates.values())

    @classmethod
    def getEntityTree(cls, templateIndex: int) -> list[dict]:
        """Return the navigation tree for entity_type.

        Keys:
        - id      : stable identifier used in fetchEntitiesByGroup
        - label   : human-readable display name
        - icon    : optional emoji / single unicode character
        - children: child items
        """
        if templateIndex not in cls._templateProvider:
            raise KeyError(f"No provider for template {templateIndex}")
        providerName = cls._templateProvider[templateIndex]
        provider = cls._registry[providerName]
        template = cls._templates[templateIndex]
        return provider.getEntitiesTree(template.getName())

    @classmethod
    def fetchEntitiesByGroup(cls, templateIndex: int, group_id: str) -> list[EntityBase]:
        """Return entities belonging to group_id for the given entity_type.

        Keys:
        - id         : passed back to the pipeline as the entity value
        - name       : displayed in the Name column
        - status     : displayed as a coloured badge (optional)
        - description: displayed in the Description column (optional)
        """
        if templateIndex not in cls._templateProvider:
            raise KeyError(f"No provider for template {templateIndex}")
        providerName = cls._templateProvider[templateIndex]
        provider = cls._registry[providerName]
        template = cls._templates[templateIndex]
        entitiesByGroup = provider.fetchEntitiesByGroup(template.getName(), group_id)
        for entity in entitiesByGroup:
            if not EntityCache.contains(templateIndex, entity.id):
                EntityCache.add(templateIndex, entity)
        return entitiesByGroup
