// NavigationButton.qml
// Component used to align text and icon in a button 

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import MaterialIcons 2.2

Button {
    id: root

    // Use non-conflicting names but expose them cleanly
    property string navIcon: ""
    property string navIconPosition: "right"  // "left" or "right"
    property int navIconSize: font.pixelSize + 2
    property int navSpacing: 6

    contentItem: Row {
        spacing: root.navSpacing
        anchors.centerIn: parent

        Label {
            visible: root.navIcon !== "" && root.navIconPosition === "left"
            text: root.navIcon
            font.family: MaterialIcons.fontFamily
            font.pixelSize: root.navIconSize
            anchors.verticalCenter: parent.verticalCenter
        }

        Label {
            visible: root.text !== ""
            text: root.text
            font: root.font
            anchors.verticalCenter: parent.verticalCenter
        }

        Label {
            visible: root.navIcon !== "" && root.navIconPosition === "right"
            text: root.navIcon
            font.family: MaterialIcons.fontFamily
            font.pixelSize: root.navIconSize
            anchors.verticalCenter: parent.verticalCenter
        }
    }
}