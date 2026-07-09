import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15

ApplicationWindow {
    id: root
    title: "Pipeline Batcher UI"
    width: 900
    height: 680
    minimumWidth: 700
    minimumHeight: 520

    Material.theme: Material.Dark
    Material.accent: Material.Blue

    // Keep on top of Meshroom main window
    flags: Qt.Window | Qt.WindowStaysOnTopHint

    // --- Toolbar ---
    header: ToolBar {
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 12

            Label {
                text: {
                    switch (stack.currentIndex) {
                        case 0: return "Choose Template"
                        case 1: return "Select Entities"
                        case 2: return "Set Parameters"
                        default: return ""
                    }
                }
                font.pixelSize: 15
                font.weight: Font.Medium
            }

            Item { Layout.fillWidth: true }

            // Step indicators
            Repeater {
                id: stepsIndicator
                model: ["Template", "Entities", "Parameters"]
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

        // TODO : ParameterPage placeholder
        Item {
            id: parameterPagePlaceholder
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
    Rectangle {
        id: statusMsg
        visible: false
        width: snackLabel.implicitWidth + 40
        height: 42
        radius: 6
        color: "#2979FF"

        anchors {
            bottom: parent.bottom
            horizontalCenter: parent.horizontalCenter
            bottomMargin: 12
        }

        function show(msg, duration) {
            snackLabel.text = msg
            visible = true
            hideTimer.interval = duration || 3000
            hideTimer.restart()
        }

        Label {
            id: snackLabel
            anchors.centerIn: parent
            color: "white"
            font.pixelSize: 13
        }

        Timer {
            id: hideTimer
            onTriggered: statusMsg.visible = false
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
