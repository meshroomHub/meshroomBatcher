import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15
import MaterialIcons 2.2

Item {
    id: root

    property var    nodeData:      ({})
    property string activeGroupId: ""
    property int    depth:         0
    property color textColor

    signal groupSelected(string id)

    property bool expanded: _subtreeContains(nodeData, activeGroupId)

    width:  parent ? parent.width : 200
    height: nodeRow.height + (expanded && hasChildren ? childrenColumn.implicitHeight : 0)

    readonly property bool hasChildren: Array.isArray(nodeData.children) && nodeData.children.length > 0
    readonly property bool isActive:    !!nodeData.id && nodeData.id === activeGroupId

    function _subtreeContains(node, id) {
        if (!node || !node.id) return false
        if (node.id === id) return true
        if (!Array.isArray(node.children)) return false
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

        color:  isActive ? "#1a3a6e" : (hoverArea.containsMouse ? "#2a2a2a" : "transparent")

        Behavior on color { ColorAnimation { duration: 100 } }

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
                    color: root.textColor
                }
            }

            Label {
                visible: !!nodeData.icon
                text:    nodeData.icon || ""
                font.pixelSize: 14
                color: isActive ? "white" : root.textColor
            }

            Label {
                Layout.fillWidth: true
                text: nodeData.label || nodeData.id || ""
                font.pixelSize: 13
                font.weight: isActive ? Font.Medium : Font.Normal
                color: isActive ? "white" : Qt.lighter(root.textColor, 1.5)
                elide: Text.ElideRight
            }

            Rectangle {
                visible: root.hasChildren
                height: 18
                width:  childCountLabel.implicitWidth + 10
                radius: 9
                color:  "#333"
                Label {
                    id: childCountLabel
                    anchors.centerIn: parent
                    text: Array.isArray(nodeData.children) ? nodeData.children.length : 0
                    font.pixelSize: 10
                    color: root.textColor
                }
            }
        }

        MouseArea {
            id: hoverArea
            anchors.fill: parent
            hoverEnabled: true
            onClicked: {
                if (root.hasChildren)
                    root.expanded = !root.expanded
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