import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15
import MaterialIcons 2.2
import PBComponents 1.0

Rectangle {
    id: root

    property var checkedIds: ({})
    property string entityType: ""

    signal entityDeselected(string id)

    readonly property var idList: Object.keys(checkedIds)
    readonly property int count: idList.length

    height: 45
    radius: 8
    color: PBColors.interpolate(Material.backgroundColor, Material.accent, 0.2)
    border.color: Material.accent
    border.width: 1
    clip: true

    RowLayout {
        anchors {
            fill: parent
            leftMargin: 12
            rightMargin: 12
        }
        spacing: 10

        // Count label
        Label {
            text: root.count + " selected"
            font.pixelSize: 12
            font.weight: Font.Medium
            color: Material.accent
            Layout.preferredWidth: implicitWidth
        }

        Rectangle { width: 1; height: 28; color: "#2a4a6a" }

        // Scrollable row
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            ScrollBar.vertical.policy: ScrollBar.AlwaysOff
            ScrollBar.horizontal.policy: ScrollBar.AsNeeded

            ScrollBar.horizontal.height: 10
            ScrollBar.horizontal.contentItem: Rectangle {
                radius: 10
                color: parent.pressed ? Material.accent : parent.hovered
                    ? Qt.alpha(Material.accent, 0.7)
                    : Qt.alpha(Material.accent, 0.3)
                Behavior on color { ColorAnimation { duration: 100 } }
            }

            Row {
                id: scrollRow
                spacing: 6
                anchors.verticalCenter: parent.verticalCenter
                padding: 4

                Repeater {
                    model: root.idList

                    delegate: Rectangle {
                        height: root.height - parent.padding - 10
                        width: rowLayout.implicitWidth + rowLayout.anchors.leftMargin + rowLayout.anchors.rightMargin
                        radius: 13
                        color: PBColors.secondary
                        border.color: Qt.darker(PBColors.secondary, 1.4)
                        border.width: 1
                        anchors.verticalCenter: parent.verticalCenter

                        RowLayout {
                            id: rowLayout
                            anchors {
                                fill: parent
                                leftMargin: 8
                                rightMargin: 4
                            }
                            spacing: 4

                            Label {
                                id: selectedItemLabel
                                text: modelData
                                font.pixelSize: 11
                                color: PBColors.textOnSecondary
                                elide: Text.ElideLeft
                                Layout.maximumWidth: 150
                            }

                            Rectangle {
                                width: 16; height: 16
                                radius: 8
                                color: removeHover.containsMouse ? "#cc3333" : "transparent"
                                Behavior on color { ColorAnimation { duration: 80 } }

                                Label {
                                    anchors.centerIn: parent
                                    text: MaterialIcons.close
                                    font.pixelSize: 12
                                    color: removeHover.containsMouse ? "white" : "#888"
                                }

                                MouseArea {
                                    id: removeHover
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    onClicked: root.entityDeselected(modelData)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
