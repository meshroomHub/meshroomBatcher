# -*- coding: utf-8 -*-

"""
imageFoldersProvider - Provider for image folders.

It works using these environment variables:
- `MR_BATCHER_TEMPLATES_DIR`: semicolon-sparated folders containing .mg files
- `MR_BATCHER_OUTPUT_ROOT`: root path where instanciated files are created
- `MR_BATCHER_IMGFOLDER_ROOT`: file explorer root path
"""

# ========== Py standard lib imports ==========
import os
import copy
import logging
from pathlib import Path

# ========== Meshroom imports ==========
from meshroom.core.graph import Graph

# ========== Imports from current package ==========
from pipelineBatcher.utilities import PathTemplate
from pipelineBatcher.entityProvider import (
    EntityBase,
    TemplateInfo,
    EntityProvider,
    EntityProviderRegistry
)


def fetchAllTemplateScenes():
    templateFolders = os.getenv("MR_BATCHER_TEMPLATES_DIR", "").split(":")
    templateFolders.append(os.getenv("MESHROOM_BATCHER_RESOURCES"))
    templateFolders = [Path(p) for p in templateFolders if p and os.path.exists(p)]
    for folder in templateFolders:
        meshroomFiles = [p for p in folder.iterdir() if p.suffix == ".mg"]
        for p in meshroomFiles:
            yield str(p)


def buildTemplates() -> dict[str, TemplateInfo]:
    templates = {}
    lastIndex = 0
    for path in fetchAllTemplateScenes():
        data = {
            "template": path,
            "input_entity_type": "ImageFolder",
            "input_entity_params": {},
            "description": f"Pipeline {path}",
        }
        tpl = TemplateInfo.fromDict(data)
        templates[f"{lastIndex:02d}_{tpl.getName()}"] = tpl
    return templates


class ImageFolderTree:
    def __init__(self):
        self.root = os.getenv("MR_BATCHER_IMGFOLDER_ROOT", "")
        if not os.path.exists(self.root):
            logging.error("MR_BATCHER_IMGFOLDER_ROOT should be set to a real path.")
            self.root = None
        self.filterExt = [".jpg", ".jpeg", ".png", ".exr"]
        self._tree = None

    def _hasImages(self, folder: Path) -> bool:
        """Check if a folder contains any file with accepted extensions"""
        try:
            return any(
                file.suffix.lower() in self.filterExt for file in folder.iterdir() if file.is_file()
            )
        except PermissionError:
            return False

    def _buildNode(self, path: str, remainingMaxDepth=5) -> dict:
        """Recursively build a node for the given path"""
        if path is None:
            return {
                "id": "None",
                "label": "",
                "icon": "",
                "hasImages": False,
                "children": []
            }
        node = {
            "id": str(path),
            "label": Path(path).stem.replace("_", " "),
            "icon": "\ue2c7",
            "hasImages": self._hasImages(Path(path)),
            "children": []
        }

        if remainingMaxDepth <= 0:
            return node

        # Recursively add children
        try:
            for entry in os.scandir(path):
                try:
                    if entry.is_dir():
                        node["children"].append(self._buildNode(entry.path, remainingMaxDepth=remainingMaxDepth - 1))
                except:
                    pass
        except PermissionError:
            pass

        return node

    def _prune(self, node: dict) -> bool:
        """Remove nodes that have neither images nor a child with an image.
        Returns True if the node should be kept, False if it should be pruned.
        """
        # Recursively prune children first
        node["children"] = [
            child for child in node["children"]
            if self._prune(child)
        ]

        # Keep this node if it has images or has remaining children
        return node["hasImages"] or len(node["children"]) > 0

    def getTree(self) -> dict:
        """Build and return the image folder tree, using cached version if available"""
        if self._tree is None:
            self._tree = self._buildNode(self.root)
            self._prune(self._tree)
        return self._tree

    def getEntityTree(self, root: dict = None) -> dict:
        if root is None:
            tree = self.getTree()
            root = copy.deepcopy(tree)
        entityTree = {}
        for k in root.keys():
            if k in ("id", "label", "icon"):
                entityTree[k] = root[k]
            if k == "children":
                entityTree[k] = [self.getEntityTree(root=child) for child in root["children"]]
        return entityTree

    def getNode(self, root, nodeId):
        if root["id"] == nodeId:
            return root
        for n in root.get("children", []):
            foundNode = self.getNode(n, nodeId)
            if foundNode:
                return foundNode
        return None


class ImageFolderProvider(EntityProvider):
    name = "ImageFolderProvider"
    entityType = "ImageFolder"
        
    def __init__(self):
        self._root = os.getenv("MR_BATCHER_OUTPUT_ROOT", f"/tmp/meshroomBatcher/{self.name}")
        self._path_template = "{root}/{templateName}/{entity_name}-v{version}.mg"
        self._templates = buildTemplates()
        self._imageFolderTree = ImageFolderTree()

    def listAvailableTemplates(self) -> list[TemplateInfo]:
        return list(self._templates.values())

    def getEntitiesTree(self, templateName: str) -> list[dict]:
        tree = self._imageFolderTree.getEntityTree()
        return tree.get("children", [])

    def fetchEntitiesByGroup(self, templateName: str, group_id: str) -> list[EntityBase]:
        tree = self._imageFolderTree.getTree()
        selectedNode = self._imageFolderTree.getNode(tree, group_id)
        if not selectedNode:
            return []
        group_entities = []
        for n in selectedNode["children"]:
            if not n["hasImages"]:
                continue
            path = n["id"]
            imgExts = set(
                e for e in map(lambda x: x.suffix, Path(path).iterdir()) 
                if e.lower() in self._imageFolderTree.filterExt
            )
            status = list(imgExts)[0][1:] if imgExts else ""
            group_entities.append(EntityBase(
                entity_type="folder",
                entity_name=n["label"],
                id=path,
                status=status,
                description=f"Image folder {n['id']}"
            ))
        return group_entities

    def generateScenePath(self, templateName: str, entity: EntityBase):
        pathTpl = PathTemplate(self._path_template)
        logging.info(f"path template: {pathTpl}")
        fields = {
            "root": self._root,
            "templateName": templateName,
            "entity_name": entity.entity_name
        }
        files = pathTpl.listFiles(fields)
        logging.info(f"{len(files)} existing version:")
        for file in files:
            logging.info(f"- {file}")
        scene = pathTpl.getNextPath(fields)
        return scene
    
    @staticmethod
    def updateEntityOnGraph(template: TemplateInfo, graph: Graph, entity: EntityBase):
        imageFolder = entity.id
        logging.info(f"Update graph from image folder {imageFolder}")
        # Fetch input nodes
        inputNodes = graph.findInputNodes()
        # Fetch input nodes
        for inputNode in inputNodes:
            # Initialize the input nodes with the image folder
            inputNode.nodeDesc.initialize(inputNode, [imageFolder], [])

EntityProviderRegistry.register(ImageFolderProvider())
