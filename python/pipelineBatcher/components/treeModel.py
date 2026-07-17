from PySide6.QtCore import (
    QAbstractItemModel,
    QModelIndex,
    Qt,
    Slot,
)


class TreeNode:
    """Tree node object."""

    __slots__ = ("nodeId", "label", "icon", "entity_count", "children", "parent")

    def __init__(self, nodeId: str, label: str, icon: str, entity_count: int, parent: "TreeNode | None"):
        self.nodeId = nodeId
        self.label = label
        self.icon = icon
        self.entity_count = entity_count
        self.children: list[TreeNode] = []
        self.parent = parent

    def rowIndex(self) -> int:
        """This node's row index within its parent's children list."""
        if self.parent is None:
            return 0
        return self.parent.children.index(self)


class EntityTreeModel(QAbstractItemModel):
    """
    Tree model.
    Leaf nodes are pruned from the tree, to only display node with children.
    """

    IdRole = Qt.UserRole + 1
    LabelRole = Qt.UserRole + 2
    IconRole = Qt.UserRole + 3
    EntityCountRole = Qt.UserRole + 4
    HasChildrenRole = Qt.UserRole + 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self._root = TreeNode(nodeId="", label="", icon="", entity_count=0, parent=None)

    def roleNames(self) -> dict:
        return {
            Qt.DisplayRole: b"display",
            self.IdRole: b"id",
            self.LabelRole: b"label",
            self.IconRole: b"icon",
            self.EntityCountRole: b"entityCount",
            self.HasChildrenRole: b"hasChildren",
        }

    def data(self, index: "QModelIndex", role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        node: TreeNode = index.internalPointer()
        if role in (Qt.DisplayRole, self.LabelRole):
            return node.label
        if role == self.IdRole:
            return node.nodeId
        if role == self.IconRole:
            return node.icon
        if role == self.EntityCountRole:
            return node.entity_count
        if role == self.HasChildrenRole:
            return len(node.children) > 0
        return None

    def index(self, row: int, column: int, parent: "QModelIndex" = QModelIndex()) -> "QModelIndex":
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parent_node = parent.internalPointer() if parent.isValid() else self._root
        if row < 0 or row >= len(parent_node.children):
            return QModelIndex()
        return self.createIndex(row, column, parent_node.children[row])

    def parent(self, index: "QModelIndex") -> "QModelIndex":
        if not index.isValid():
            return QModelIndex()
        node: TreeNode = index.internalPointer()
        parent_node = node.parent
        if parent_node is None or parent_node is self._root:
            return QModelIndex()
        return self.createIndex(parent_node.rowIndex(), 0, parent_node)

    def rowCount(self, parent: "QModelIndex" = QModelIndex()) -> int:
        parent_node = parent.internalPointer() if parent.isValid() else self._root
        return len(parent_node.children)

    def columnCount(self, parent: "QModelIndex" = QModelIndex()) -> int:
        return 1

    def buildChildTree(self, nodes: list, parent: TreeNode) -> list[TreeNode]:
        """Recursively build pruned TreeNode children.
        A node is shown in the tree as long as it has at least one raw
        child. Its original child count is preserved.
        """
        out: list[TreeNode] = []
        for raw in nodes or []:
            raw_children = raw.get("children") or []
            if not raw_children:
                continue
            node = TreeNode(
                nodeId=raw["id"],
                label=raw.get("label", ""),  # TODO: id to label
                icon=raw.get("icon", ""),
                entity_count=len(raw_children),
                parent=parent,
            )
            node.children = self.buildChildTree(raw_children, node)
            out.append(node)
        return out

    @Slot(list)
    def load(self, rawTree: list) -> None:
        """Rebuild the model from a dict.
        The keys required are :
        - id
        - label
        - icon
        - children
        """
        self.beginResetModel()
        self._root = TreeNode(nodeId="", label="", icon="", entity_count=0, parent=None)
        self._root.children = self.buildChildTree(rawTree, self._root)
        self.endResetModel()

    @Slot(QModelIndex, result=str)
    def idForIndex(self, index: "QModelIndex") -> str:
        if not index.isValid():
            return ""
        return index.internalPointer().nodeId
