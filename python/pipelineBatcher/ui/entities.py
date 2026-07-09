"""
Entities Helper for the Pipeline Batcher UI
"""

# ========== Py standard lib imports ==========
import logging
from typing import Any

# ========== Imports from current package ==========


class EntityProvider:
    ...


def get_entities_tree(entity_type: str) -> list[dict]:
    """Return the navigation tree for entity_type.

    Keys:
    - id      : stable identifier used in fetchEntitiesByGroup
    - label   : human-readable display name
    - icon    : optional emoji / single unicode character
    - children: child items
    """

    return EntityProvider.get_entities_tree(entity_type)

 
def fetch_entities_by_group(entity_type: str, group_id: str) -> list[dict]:
    """Return entities belonging to group_id for the given entity_type.

    Keys:
    - id         : passed back to the pipeline as the entity value
    - name       : displayed in the Name column
    - status     : displayed as a coloured badge (optional)
    - description: displayed in the Description column (optional)
    """

    return EntityProvider.fetch_entities_by_group(entity_type, group_id)
