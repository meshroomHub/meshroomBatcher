// 
// Instanciation work in 2 modes:
// If the UI is opened in Mehsroom then it uses the _currentScene
// context property set by MeshroomApp to create the graph
// in the current scene?
// If the UI is opened in standalone mode, then instanciation
// take place in different files.
// 

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15
import MaterialIcons 2.2
import PBComponents 1.0


Item {
    id: root

    property var instanciator: pipelineBatcherBackend.instanciator

    // --- State ---
    property string statusText: ""
    property int  _currentEntity: 0
    property int  offset: 0
    property bool _running: false
    property bool _finished: false

    function processAll() {
        if (_running) return
        _currentEntity = 0
        offset = 0
        _running = true
        _finished = false
        statusText = "Starting..."
        _processNext()
    }

    // --- Callback for opening a created scene ---
    function openScene(filePath) {
        // TODO
    }

    // --- Run on an entity ---
    function _processNext() {
        var total = instanciator.entityCount()
        if (_currentEntity >= total) {
            _running = false
            _finished = true
            statusText = "Done — " + total + " instance(s) created."
            // pipelineBatcherBackend.next()
            return
        }

        statusText = "Creating instance " + (_currentEntity + 1) + " / " + total + "..."

        // Create nodes
        var nodes = instanciator.createInstanceForEntity(_currentEntity, offset)

        if (!nodes || nodes.length === 0) {
            statusLabel = "Error on entity " + _currentEntity
            _running = false
            return
        }

        if (instanciator.mode == "LIVE_SCENE") {
            // Compute bounding box
            var padding = _currentScene.layout.gridSpacing * 0.5
            var minX =  Number.MAX_VALUE,  minY =  Number.MAX_VALUE
            var maxX = -Number.MAX_VALUE,  maxY = -Number.MAX_VALUE

            for (var k = 0; k < nodes.length; k++) {
                var n = nodes[k]
                var nw = n.nodeWidth  > 0 ? n.nodeWidth  : _currentScene.layout.nodeWidth
                var nh = n.nodeHeight > 0 ? n.nodeHeight : _currentScene.layout.nodeHeight
                minX = Math.min(minX, n.x);  minY = Math.min(minY, n.y)
                maxX = Math.max(maxX, n.x + nw);  maxY = Math.max(maxY, n.y + nh)
            }

            var bboxX = minX - padding
            var bboxY = minY - 2 * padding
            var bboxW = Math.round(maxX - minX + 2 * padding)
            var bboxH = Math.round(maxY - minY + 3 * padding)

            // Create Backdrop wrapping the created pipeline instance
            var backdrop = _currentScene.addBackdropNode(Qt.point(bboxX, bboxY), bboxW, bboxH)
            // Set backdrop label
            instanciator.setBackdropName(backdrop, instanciator.entityLabel(_currentEntity))
            // Update the Y padding for next instance and iterate
            offset = Math.round(maxY + padding * 4)
        }

        _currentEntity++
        iterTimer.restart()
    }

    Timer {
        id: iterTimer
        interval: 50
        repeat: false
        onTriggered: _processNext()
    }

    // --- UI ---
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 16

        Item { Layout.fillHeight: true }

        BusyIndicator {
            Layout.alignment: Qt.AlignHCenter
            running: _running
        }

        Label {
            Layout.alignment: Qt.AlignHCenter
            font.pixelSize: 14
            text: root.statusText
        }

        ProgressBar {
            Layout.preferredWidth: 300
            Layout.alignment: Qt.AlignHCenter
            visible: instanciator !== null && !(_finished && instanciator.mode === "UNIQUE_FILES")
            value: instanciator ? _currentEntity / instanciator.entityCount() : 0
        }

        ListView {
            Layout.fillWidth: true
            Layout.preferredHeight: 200
            clip: true
            visible: _finished && instanciator && instanciator.mode === "UNIQUE_FILES"
            model: instanciator ? instanciator.createdFiles : null
            spacing: 4
            delegate: Button {
                width: ListView.view.width
                flat: true

                onClicked: root.openScene(filePath)

                contentItem: RowLayout {
                    spacing: 10

                    MaterialLabel {
                        text: MaterialIcons.movie
                        font.pixelSize: 18
                        color: parent.parent.hovered ? PBColors.hoveredText : PBColors.textColor
                    }

                    Label {
                        text: entityName
                        Layout.preferredWidth: 150
                        elide: Text.ElideRight
                        font.bold: true
                    }

                    Label {
                        text: filePath
                        elide: Text.ElideMiddle
                        Layout.fillWidth: true
                        opacity: 0.7
                    }
                }

                background: Rectangle {
                    radius: 4
                    color: parent.hovered ? Qt.lighter(PBColors.secondary, 1.2) : "transparent"
                    border.color: PBColors.primary
                    border.width: 1
                }
            }
        }

        Item { Layout.fillHeight: true }

        // Bottom bar
        RowLayout {
            Layout.fillWidth: true

            Item { Layout.fillWidth: true }

            NavigationButton {
                text: "Close the UI"
                navIcon: MaterialIcons.celebration
                Material.background: hovered ? PBColors.startButton     : Material.accent
                Material.foreground: hovered ? PBColors.startButtonText : Material.textColor
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
