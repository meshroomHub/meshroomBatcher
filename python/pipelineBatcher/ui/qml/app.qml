import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15
import PBComponents 1.0
import MaterialIcons 2.2

ApplicationWindow {
    id: root
    title: "Pipeline Batcher UI"
    width: 900
    height: 680
    minimumWidth: 700
    minimumHeight: 520

    property bool darkTheme: true

    Material.theme: darkTheme ? Material.Dark : Material.Light
    Material.accent: Material.Blue
    Material.primary: "#2b58ac"  // Toolbar color

    // Keep on top of Meshroom main window
    flags: Qt.Window | Qt.WindowStaysOnTopHint

    // --- Toolbar ---
    header: ToolBar {
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 12

            Material.background: "#0e1b64"

            Switch {
                Layout.fillHeight: true
                implicitWidth: 80  // Fix the width to avoid moving other components on animation
                indicator.scale: 0.7  // Make the switch smaller

                text: root.darkTheme ? MaterialIcons.dark_mode : MaterialIcons.light_mode
                checked: !root.darkTheme
                onClicked: root.darkTheme = !root.darkTheme

                font.pixelSize: 20
                leftPadding: 20

                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: root.darkTheme ? "#ccc" : "#fff"
                    verticalAlignment: Text.AlignVCenter
                    // Fine tuned padding
                    topPadding: 5
                    // Switch the icon from left to right
                    leftPadding: root.darkTheme ? parent.width - width - 45 : parent.indicator.width  - 5
                    Behavior on leftPadding {
                        NumberAnimation {
                            duration: 250
                            easing.type: Easing.InOutQuad
                        }
                    }
                }
            }

            Item { Layout.fillWidth: true }  // Spacer

            Label {
                text: {
                    switch (stack.currentIndex) {
                        case 0: return "Choose Template"
                        case 1: return "Select Entities"
                        case 2: return "Set Parameters"
                        case 3: return "Done"
                        default: return ""
                    }
                }
                color: "white"
                font.pixelSize: 15
                font.weight: Font.Medium
            }

            Item { Layout.fillWidth: true }  // Spacer

            // Step indicators
            Repeater {
                id: stepsIndicator
                model: ["Template", "Entities", "Parameters", "Done"]
                delegate: RowLayout {
                    spacing: 4

                    // Circle with the step index
                    Rectangle {
                        width: 22
                        height: 22
                        radius: 11
                        color: index <= stack.currentIndex ? Material.accent : "#555"
                        Label {
                            anchors.centerIn: parent
                            text: index + 1
                            font.pixelSize: 11
                            color: "white"
                        }
                    }

                    // Name of the step
                    Label {
                        text: modelData
                        font.pixelSize: 11
                        color: index <= stack.currentIndex ? "white" : "#888"
                    }

                    // Connector line
                    Rectangle {
                        visible: index < stepsIndicator.count - 1
                        width: 18; height: 2
                        color: index < stack.currentIndex ? Material.accent : "#555"
                    }
                }
            }

            Item { width: 8 }
        }
    }

    // --- Layout ---
    StackLayout {
        id: stack
        anchors.fill: parent
        currentIndex: 0  // driven by onPageChanged

        TemplatePage {
            id: templatePage
        }

        EntityPage {
            id: entityPage
        }

        ParameterPage {
            id: parameterPage
        }

        Item {
            id: donePage

            ColumnLayout {
                width: parent.width
                anchors.fill: parent
                anchors.margins: 20
                spacing: 12

                Label {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    text: "You are done !"
                    font.pixelSize: 20
                    color: "#aaa"
                }

                // Bottom bar
                RowLayout {
                    Layout.fillWidth: true

                    Item { Layout.fillWidth: true }

                    NavigationButton {
                        text: "Close the UI"
                        navIcon: MaterialIcons.celebration
                        Material.background: hovered ? "#43d668" : "#2a67ad" 
                        Material.foreground: hovered ? "#424242" : "#e0e0e0"
                        scale: hovered ? 1.25 : 1.2
                        Behavior on scale {
                            NumberAnimation { duration: 100 }
                        }
                        highlighted: hovered
                        onClicked: pipelineBatcherBackend.next()
                    }

                    Item { Layout.fillWidth: true }
                }
            }
        }

        function displayPageMessage() {
            if (currentIndex == 0)
                statusMsg.show("Please select a template")
            else if (currentIndex == 1)
                statusMsg.show("Select entities")
            else if (currentIndex == 2 && pipelineBatcherBackend.hasParametersPage())
                statusMsg.show("Fill the required parameters")
        }

        onCurrentIndexChanged: displayPageMessage()
        Component.onCompleted: displayPageMessage()
    }

    // --- Busy Overlay ---
    Rectangle {
        id: busyOverlay
        parent: Overlay.overlay  // ← attach to the QML overlay layer
        anchors.fill: parent
        color: "#80000000"
        visible: false
        z: 100

        property string busyMessage: ""

        Column {
            anchors.centerIn: parent
            spacing: 16

            BusyIndicator {
                anchors.horizontalCenter: parent.horizontalCenter
                running: busyOverlay.visible
            }
            Label {
                anchors.horizontalCenter: parent.horizontalCenter
                text: busyOverlay.busyMessage
                font.pixelSize: 14
                color: "white"
            }
        }
    }

    // --- Error Dialog ---
    Dialog {
        id: errorDialog
        property string message: ""
        title: "Error"
        modal: true
        standardButtons: Dialog.Ok
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: 400

        Label {
            text: errorDialog.message
            wrapMode: Text.Wrap
            width: parent.width
        }
    }

    // --- Status snackbar ---
    Snackbar {
        id: statusMsg

        anchors {
            bottom: parent.bottom
            horizontalCenter: parent.horizontalCenter
            bottomMargin: 20
        }
    }

    Component.onCompleted: {
        var page = pipelineBatcherBackend.page
        if (page > 0) { 
            entityPage.entityType = pipelineBatcherBackend.entityType
        }
        stack.currentIndex = page
    }

    // --- Connections ---
    Connections {
        target: pipelineBatcherBackend

        function onCloseRequested() {
            root.close()
        }

        function onPageChanged(page) {
            stack.currentIndex = page
        }

        // Forward the selected template's entity type to EntityPage
        function onTemplateSelected(entityType) {
            entityPage.entityType = entityType
        }

        function onBusyChanged(busy) {
            busyOverlay.visible = busy
        }

        function onBusyMessageChanged(message) {
            busyOverlay.busyMessage = message
        }

        function onErrorOccurred(msg) {
            busyOverlay.visible = false
            busyOverlay.busyMessage = msg
            errorDialog.message = msg
            errorDialog.open()
        }
    }
}
