import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15
import PBComponents 1.0

Rectangle {
    id: root

    // Input properties
    property int templateIndex
    property var templateModelData
    property int selectedIndex: -1

    // Signals back to TemplatePage
    signal selected(int idx)   // single click
    signal confirmed(int idx)  // double click
    
    height: templateContent.implicitHeight + 24
    radius: 8

    // Color settings
    property color backgroundColor: PBColors.backgroundColor
    color: PBColors.interpolate(backgroundColor, PBColors.accent, selectedIndex === templateIndex ? 0.3 : 0)
    border.color: selectedIndex === templateIndex ? PBColors.accent : "transparent"
    border.width: selectedIndex === templateIndex ? 2 : 0

    // Hover state
    property bool hovered: false

    Rectangle {
        anchors.fill: parent
        radius: parent.radius
        opacity: parent.hovered ? 0.3 : 0
        color: Qt.lighter(root.color, 2)
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        onEntered: root.hovered = true
        onExited: root.hovered = false
        onClicked: root.selected(templateIndex)
        onDoubleClicked: root.confirmed(templateIndex)
    }

    RowLayout {
        id: templateContent
        anchors {
            left: parent.left
            right: parent.right
            verticalCenter: parent.verticalCenter
            leftMargin: 16
            rightMargin: 16
        }
        spacing: 16

        // Entity type badge
        Rectangle {
            width: 48; height: 48
            radius: 8
            color: PBColors.entityColor(templateModelData.input_entity_type)

            Label {
                anchors.centerIn: parent
                text: templateModelData.input_entity_type
                        ? templateModelData.input_entity_type.substring(0, 2).toUpperCase()
                        : "??"
                font.pixelSize: 14
                font.weight: Font.Bold
                color: "white"
            }
        }

        // Text
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2

            Label {
                text: templateModelData.name || "(unnamed)"
                font.pixelSize: 14
                font.weight: Font.Medium
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
            Label {
                text: templateModelData.description || ""
                font.pixelSize: 12
                color: PBColors.tertiaryText
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
        }

        // Entity type indicator
        Rectangle {
            height: 22
            width: entityTypeLabel.implicitWidth + 16
            radius: 11
            color: PBColors.entityColor(templateModelData.input_entity_type)
            opacity: 0.85

            Label {
                id: entityTypeLabel
                anchors.centerIn: parent
                text: templateModelData.input_entity_type || "?"
                font.pixelSize: 11
                color: "white"
            }
        }

        // Parameter count
        Label {
            text: (templateModelData.parameters ? templateModelData.parameters.length : 0)
                    + " param(s)"
            font.pixelSize: 11
            color: PBColors.tertiaryText
        }
    }
}
