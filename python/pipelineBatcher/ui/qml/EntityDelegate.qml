import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15
import PBComponents 1.0

Rectangle {
    id: root

    property var entityData  // {id, name, status, description, **kwargs}
    property bool checked: false
    property color textColor

    signal toggled(string id)

    height: 40
    color: checked ? "#1a3a6e" : (hoverArea.containsMouse ? "#262626" : "transparent")
    radius: 4

    Behavior on color {
        ColorAnimation { duration: 150 }
    }

    // Check from the whole line
    MouseArea {
        id: hoverArea
        anchors.fill: parent
        hoverEnabled: true
        onClicked: root.toggled(root.entityData.id)
    }

    // Bottom separator
    Rectangle {
        anchors.bottom: parent.bottom
        width: parent.width
        height: 1
        color: "#2a2a2a"
    }

    RowLayout {
        id: entityRow
        anchors.fill: parent
        anchors.leftMargin: 8
        anchors.rightMargin: 12
        spacing: 0

        CheckBox {
            Layout.preferredWidth: 36
            Layout.fillHeight: true
            id: checkbox
            checked: root.checked
            onToggled: root.toggled(root.entityData.id)
        }

        Label {
            Layout.preferredWidth: 200
            Layout.fillWidth: true
            Layout.fillHeight: true
            verticalAlignment: Text.AlignVCenter
            text: entityData.name || entityData.id
            font.pixelSize: 13
            font.weight: root.checked ? Font.Medium : Font.Normal
            color: root.checked ? "white" : Qt.lighter(root.textColor, 1.5)
            elide: Text.ElideRight
            leftPadding: 4
        }

        // Status badge
        Rectangle {
            Layout.preferredWidth: 90
            Layout.fillHeight: true
            color: "transparent"

            Rectangle {
                anchors.verticalCenter: parent.verticalCenter
                visible: entityData.status !== undefined && entityData.status !== ""
                height: 20
                width: statusLabel.implicitWidth + 14
                radius: 10
                color: PBColors._statusColor(entityData.status)
                opacity: 0.85

                Label {
                    id: statusLabel
                    anchors.centerIn: parent
                    text: entityData.status || ""
                    font.pixelSize: 10
                    font.weight: Font.Medium
                    color: "white"
                }
            }
        }

        // Description
        Label {
            Layout.fillWidth: true
            Layout.fillHeight: true               // Stretches bounding box to 40px
            verticalAlignment: Text.AlignVCenter  // Centers text within the bounding box
            text: entityData ? (entityData.description || "") : ""
            font.pixelSize: 12
            color: root.textColor
            elide: Text.ElideRight
        }
    }
}