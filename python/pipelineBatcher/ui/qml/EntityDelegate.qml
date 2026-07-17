import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15
import PBComponents 1.0

Rectangle {
    id: root

    property var entityData  // {id, name, status, description, **kwargs}
    property bool checked: false

    signal toggled(string id)

    height: 40
    color: checked ? PBColors.selectedBackground : (hoverArea.containsMouse ? PBColors.rowHoverBackground : "transparent")
    radius: 4

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
        color: PBColors.separator
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
            id: entityNameLabel
            // Layout.preferredWidth: 200
            Layout.fillHeight: true
            verticalAlignment: Text.AlignVCenter
            text: entityData.name || entityData.id
            font.pixelSize: 13
            font.weight: root.checked ? Font.Medium : Font.Normal
            color: Qt.lighter(PBColors.textColor, root.checked ? 0 : 1.4)
            leftPadding: 4
            rightPadding: 15
        }

        Item { Layout.fillWidth: true }

        // Status badge
        Rectangle {
            id: statusBadgeRectangle
            Layout.preferredWidth: statusBadge.visible ? statusLabel.implicitWidth + 10 : 0
            Layout.fillHeight: true
            Layout.rightMargin: statusBadge.visible ? 15 : 0
            color: "transparent"

            Rectangle {
                id: statusBadge
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
                    color: PBColors.primaryText
                }
            }
        }

        // Description
        Label {
            Layout.fillHeight: true
            verticalAlignment: Text.AlignVCenter
            text: entityData ? (entityData.description || "") : ""
            font.pixelSize: 12
            color: PBColors.tertiaryText
            elide: Text.ElideRight
        }
    }
}