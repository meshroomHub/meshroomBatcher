import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15
import MaterialIcons 2.2
import PBComponents 1.0

Item {
    id: root

    property var    nodeData:      ({})
    property string activeGroupId: ""
    property int    depth:         0

    signal groupSelected(string id)

    property var manualExpanded: null
    property bool expanded: manualExpanded !== null ? manualExpanded : _subtreeContains(nodeData, activeGroupId)

    width:  parent ? parent.width : 200
    height: nodeRow.height + (expanded && hasChildren ? childrenColumn.implicitHeight : 0)

    function _isArrayLike(v) {
        return !!v && typeof v.length === "number"
    }

    readonly property bool hasChildren: root._isArrayLike(nodeData.children) && nodeData.children.length > 0
    readonly property bool isActive:    !!nodeData.id && nodeData.id === activeGroupId
    readonly property int  entityCount: nodeData.entityCount !== undefined
                                            ? nodeData.entityCount
                                            : (root._isArrayLike(nodeData.children) ? nodeData.children.length : 0)

    function _subtreeContains(node, id) {
        if (!node || !node.id) return false
        if (node.id === id) return true
        if (!_isArrayLike(node.children)) return false
        for (var i = 0; i < node.children.length; i++) {
            if (_subtreeContains(node.children[i], id)) return true
        }
        return false
    }

    // --- Row ---
    Rectangle {
        id: nodeRow

        width:  parent.width
        height: 34
        radius: 4

        color:  isActive ? PBColors.selectedBackground : (hoverArea.containsMouse ? PBColors.hoverBackground : "transparent")

        Rectangle {
            visible: isActive

            width: 3
            height: 20
            radius: 2

            anchors {
                left: parent.left
                leftMargin: depth * 12
                verticalCenter: parent.verticalCenter
            }
            color: Material.accent
        }

        RowLayout {
            anchors {
                fill: parent
                leftMargin: depth * 12 + 10
                rightMargin: 8
            }
            spacing: 6

            Item {
                width: 16
                height: 16
                Label {
                    anchors.centerIn: parent
                    visible: root.hasChildren
                    text: root.expanded ? MaterialIcons.arrow_drop_down : MaterialIcons.arrow_right
                    font.pixelSize: 10
                    color: PBColors.textColor
                }
            }

            Label {
                visible: !!nodeData.icon
                text:    nodeData.icon || ""
                font.pixelSize: 14
                color: PBColors.textColor
            }

            Label {
                Layout.fillWidth: true
                text: nodeData.label || nodeData.id || ""
                font.pixelSize: 13
                font.weight: isActive ? Font.Medium : Font.Normal
                color: PBColors.textColor
                elide: Text.ElideRight
            }

            Rectangle {
                visible: root.entityCount > 0
                height: 18
                width:  childCountLabel.implicitWidth + 10
                radius: 9
                color:  PBColors.badgeBackground
                Label {
                    id: childCountLabel
                    anchors.centerIn: parent
                    text: root.entityCount
                    font.pixelSize: 10
                    color: PBColors.textColor
                }
            }
        }

        MouseArea {
            id: hoverArea
            anchors.fill: parent
            hoverEnabled: true
            onClicked: {
                if (root.hasChildren)
                    root.manualExpanded = !root.expanded
                if (nodeData.id)
                    root.groupSelected(nodeData.id)
            }
        }
    }

    // Container for dynamic child nodes
    Column {
        id: childrenColumn
        anchors.top: nodeRow.bottom
        width: parent.width
        visible: expanded && hasChildren

        Repeater {
            // Only generate children elements when this node is expanded
            model: (root.expanded && root.hasChildren) ? root.nodeData.children : []

            delegate: Loader {
                width: childrenColumn.width
                // Uses runtime relative loading to resolve static recursion limits
                source: "EntityTreeNode.qml"

                onLoaded: {
                    item.nodeData = modelData
                    item.activeGroupId = Qt.binding(function() { return root.activeGroupId })
                    item.depth = root.depth + 1
                    item.groupSelected.connect(function(id) { root.groupSelected(id) })
                }
            }
        }
    }
}