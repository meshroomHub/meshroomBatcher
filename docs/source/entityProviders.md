# Entity providers

## How to implement a new provider

> [!TIP]
> An `EntityProvider` demo can be found [here](../../mock/mockEntityProvider.py)

To implement a new provider you must write a class inheriting `EntityProvider`, and then register it in the `EntityProviderRegistry`:

```python
from pipelineBatcher.entityProvider import EntityBase, TemplateInfo, EntityProvider, EntityProviderRegistry

class MyEntityProvider(EntityProvider):
    name = "MyEntityProvider"
    entityType = "EntityName"

    def listAvailableTemplates(self) -> list[TemplateInfo]:
        """List templates provided by this provider."""
        ...

    def getEntitiesTree(self, templateName: str) -> list[dict]:
        """Return the navigation tree for entity_type.

        Keys:
        - id      : stable identifier used in fetchEntitiesByGroup
        - label   : human-readable display name
        - icon    : optional emoji / single unicode character
        - children: child items
        """
        ...

    def fetchEntitiesByGroup(self, templateName: str, group_id: str) -> list[EntityBase]:
        """Return entities belonging to group_id for the given entity_type.

        Keys:
        - id         : passed back to the pipeline as the entity value
        - name       : displayed in the Name column
        - status     : displayed as a coloured badge (optional)
        - description: displayed in the Description column (optional)
        """
        ...

    @staticmethod
    def updateEntityOnGraph(template: TemplateInfo, graph: Graph, entity: EntityBase):
        """Update the generated graph with the entity info."""

    def generateScenePath(self, templateName: str, entity: EntityBase):
        """Generate the scene destination path."""

EntityProviderRegistry.register(MyEntityProvider())
```
