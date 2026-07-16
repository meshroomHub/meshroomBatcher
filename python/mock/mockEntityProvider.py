# -*- coding: utf-8 -*-

"""
mockEntityProvider - Mock class to provide fake data for the batcher.
"""

import os
import glob
import re
import copy
import json
import logging
from pathlib import Path
from random import randint

from pipelineBatcher.ui.entityProvider import (
    EntityBase,
    TemplateInfo,
    EntityProvider,
    EntityProviderRegistry
)


class PathTemplate:
    def __init__(self, template: str):
        self.template = template
        self.fields = re.findall(r'\{(\w+)\}', template)

    def _check_fields(self, data: dict):
        missing = [f for f in self.fields if f != 'version' and f not in data]
        if missing:
            raise ValueError(f"Missing fields: {missing}")

    def _apply_fields(self, data: dict, version_wildcard: str = None) -> str:
        path = self.template
        for field in self.fields:
            if field == 'version':
                path = path.replace('{version}', version_wildcard if version_wildcard else data.get('version', '{version}'))
            else:
                path = path.replace(f'{{{field}}}', str(data[field]))
        return path

    def list_files(self, data: dict) -> list[str]:
        self._check_fields(data)
        pattern = self._apply_fields(data, version_wildcard='*')
        return sorted(glob.glob(pattern))

    def next_version_path(self, data: dict) -> str:
        self._check_fields(data)
        existing = self.list_files(data)

        if not existing:
            next_version = 1
        else:
            # Extract version numbers from existing files
            version_pattern = self._apply_fields(data, version_wildcard=r'(\d+)')
            versions = [
                int(m.group(1))
                for f in existing
                if (m := re.search(version_pattern, f))
            ]
            next_version = max(versions) + 1 if versions else 1

        return self._apply_fields({**data, 'version': str(next_version).zfill(3)})


def createTemplateFromPath(path: str) -> TemplateInfo:
    with open(path, "r") as f:
        data = json.load(f)
    # Remap {root} to the parent folder with the template file
    if "{root}" in data.get("template"):
        rootFolder = str(Path(path).parent)
        data["template"] = data["template"].replace("{root}", rootFolder)
    tpl = TemplateInfo.fromDict(data=data)
    # Additional keys
    tpl.pathTemplate = data.get("pathTemplate", "/tmp/{version}.mg")
    return tpl


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
            tpl = createTemplateFromPath(str(tplPath))
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
    entityType = "Shot"
        
    def __init__(self):
        self._root = os.getenv("MR_BATCHER_FILES_ROOT", f"/tmp/meshroomBatcher/{self.name}")
        self._templates: dict[str, TemplateInfo] = {t.getName(): t for t in list_templates()}
    
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

    def fetchEntitiesByGroup(self, templateName: str, group_id: str) -> list[EntityBase]:
        tree = self.getEntitiesTree(templateName)
        entities = []
        if group_id == "seq_001":
            entities = tree[0]["children"]
        elif group_id == "seq_002":
            entities = tree[1]["children"]
        elif group_id == "master_A":
            entities = []
        elif group_id == "master_a_seq_001":
            entities = tree[2]["children"][0]["children"]
        group_entities = []
        for e in entities:
            status = ("wtg", "rdy", "ip", "rev", "apr")[randint(0, 4)]
            group_entities.append(EntityBase(
                entity_type=self.entityType,
                entity_name=e["label"],
                id=e["id"],
                status=status,
                description=f"Entity {e['id']}"
            ))
        return group_entities

    def generateScenePath(self, templateName: str, entity: EntityBase):
        template = self._templates.get(templateName)
        pathTpl = PathTemplate(template.pathTemplate)
        logging.info(f"path template: {pathTpl}")
        fields = copy.deepcopy(entity.__dict__)
        del fields["id"]
        fields["root"] = self._root
        files = pathTpl.list_files(fields)
        logging.info(f"{len(files)} existing version:")
        for file in files:
            logging.info(f"- {file}")
        scene = pathTpl.next_version_path(fields)
        return scene

EntityProviderRegistry.register(MockEntityProvider())
