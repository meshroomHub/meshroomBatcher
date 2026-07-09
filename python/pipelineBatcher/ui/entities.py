"""
Entities Helper for the Pipeline Batcher UI
"""

# ========== Py standard lib imports ==========
from random import randint
import logging
from typing import Any
from pathlib import Path
from collections import OrderedDict
from types import SimpleNamespace


# ========== Imports from current package ==========


CachedEntityById = {}  # id: CachedEntity

class CachedEntity(SimpleNamespace):
    def __init__(self, entity_type, entity_name, **kwargs):
        super().__init__(**kwargs)
        self.entity_type = entity_type
        self.entity_name = entity_name
        if "id" not in kwargs:
            self.id = f"{entity_type.lower()}.{entity_name}"
        CachedEntityById[self.id] = self  # Keep the new entity in cache

    def __contains__(self, item):
        return item in self.__dict__


def get_entity(entity_id: str) -> CachedEntity:
    return CachedEntityById.get(entity_id)


class MockEntityProvider:
    @staticmethod
    def get_entities_tree(entity_type: str) -> list[dict]:
        entity_tree = []
        entity_tree.append({
            "id"      : "seq_001",
            "label"   : "Sequence 001",
            "icon"    : "\ue638",
            "children": [
                {
                    "id"      : "seq_001_shot_001",
                    "label"   : "001_001",
                    "icon"    : "\ue02c",
                    "children": [],
                }
            ]
        })
        entity_tree.append({
            "id"      : "seq_002",
            "label"   : "Sequence 002",
            "icon"    : "\ue638",
            "children": [
                {
                    "id"      : "seq_002_shot_001",
                    "label"   : "002_001",
                    "icon"    : "\ue02c",
                    "children": [],
                },
                {
                    "id"      : "seq_002_shot_002",
                    "label"   : "002_002",
                    "icon"    : "\ue02c",
                    "children": [],
                },
                {
                    "id"      : "seq_002_shot_003",
                    "label"   : "002_003",
                    "icon"    : "\ue02c",
                    "children": [],
                }
            ]
        })
        entity_tree.append({
            "id"      : "master_A",
            "label"   : "Master A",
            "icon"    : "\ue53b",
            "children": [{
                "id"      : "master_a_seq_001",
                "label"   : "Sequence 001",
                "icon"    : "\ue638",
                "children": [
                    {
                        "id"      : "A_seq_001_shot_001",
                        "label"   : "A_001_001",
                        "icon"    : "\ue02c",
                        "children": [],
                    },
                    {
                        "id"      : "A_seq_001_shot_002",
                        "label"   : "A_001_002",
                        "icon"    : "\ue02c",
                        "children": [],
                    }
                ]
            }]
        })
        return entity_tree

    @staticmethod
    def fetch_entities_by_group(entity_type: str, group_id: str) -> list[dict]:
        tree = MockEntityProvider.get_entities_tree(entity_type)
        entities = []
        if group_id == "seq_001":
            entities = tree[0]["children"]
        elif group_id == "seq_002":
            entities = tree[1]["children"]
        elif group_id == "master_A":
            entities = [{
                "id"      : "master_a_seq_001",
                "label"   : "Sequence 001",
            }]
        elif group_id == "master_a_seq_001":
            entities = tree[2]["children"][0]["children"]
        group_entities = []
        for e in entities:
            status = ("wtg", "rdy", "ip", "rev", "apr")[randint(0, 4)]
            group_entities.append({
                "id"         : e["id"],
                "name"       : e["label"],
                "status"     : status,
                "description": f"Entity {e['id']}"
            })
        return group_entities


def get_entities_tree(entity_type: str) -> list[dict]:
    """Return the navigation tree for entity_type.

    Keys:
    - id      : stable identifier used in fetchEntitiesByGroup
    - label   : human-readable display name
    - icon    : optional emoji / single unicode character
    - children: child items
    """

    return MockEntityProvider.get_entities_tree(entity_type)

 
def fetch_entities_by_group(entity_type: str, group_id: str) -> list[dict]:
    """Return entities belonging to group_id for the given entity_type.

    Keys:
    - id         : passed back to the pipeline as the entity value
    - name       : displayed in the Name column
    - status     : displayed as a coloured badge (optional)
    - description: displayed in the Description column (optional)
    """

    return MockEntityProvider.fetch_entities_by_group(entity_type, group_id)
