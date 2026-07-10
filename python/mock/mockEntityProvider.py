# -*- coding: utf-8 -*-

"""
mockEntityProvider - Mock class to provide fake data for the batcher.
"""

import os
import logging
from pathlib import Path
from random import randint

from pipelineBatcher.ui.entityProvider import (
    TemplateInfo,
    EntityProvider,
    EntityProviderRegistry
)


def list_templates() -> list[TemplateInfo]:
    """
    Scan PIPELINE_RESOURCES folder for JSON files and
    return a list with the detected templates.
    """
    results: list[TemplateInfo] = []
    # Get files
    resources = os.getenv("PIPELINE_RESOURCES")
    templatesFolder = Path(resources) / "batchPipelines"
    if not os.path.isdir(templatesFolder):
        logging.warning(f"Templates directory does not exist: {templatesFolder}")
        return results
    # Get templates
    tplPath: Path
    for tplPath in sorted(templatesFolder.iterdir()):
        if tplPath.suffix != ".json":
            continue
        try:
            tpl = TemplateInfo.fromPath(str(tplPath))
        except Exception as exc:
            logging.warning(f"Could not parse template '{tplPath}': {exc}")
        else:
            if tpl is None:
                logging.warning(f"Could not add template from {tplPath}. Check logs for more info.")
                continue
            results.append(tpl)
    logging.info(f"Found {len(results)} template(s) in '{templatesFolder}'")
    return results


class MockEntityProvider(EntityProvider):
    name = "MockEntityProvider"
    
    def __init__(self):
        self._templates: dict[str, TemplateInfo] = {t.getName(): t for t in list_templates()}
    
    def get_template(self, name) -> TemplateInfo:
        return self._templates.get(name)

    def listAvailableTemplates(self) -> list[TemplateInfo]:
        return list(self._templates.values())

    def getEntitiesTree(self, templateName: str) -> list[dict]:
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

    def fetchEntitiesByGroup(self, templateName: str, group_id: str) -> list[dict]:
        tree = self.getEntitiesTree(templateName)
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


EntityProviderRegistry.register(MockEntityProvider())
