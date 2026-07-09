// InstanciationPage.qml
// Uses the _currentScene context property set by MeshroomApp

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15
import MaterialIcons 2.2


Item {
    id: root

    property var instanciator: pipelineBatcherBackend.instanciator

    onInstanciatorChanged: {
        if (instanciator && visible)
            _runAll()
    }

    onVisibleChanged: {
        if (visible && instanciator)
            _runAll()
    }

    // --- State ---
    property int  _currentEntity: 0
    property int  _yOffset:       0
    property bool _running:       false

    // --- Run process ---
    function _runAll() {
        if (_running) return
        _currentEntity = 0
        _yOffset       = 0
        _running       = true
        statusLabel.text = "Starting..."
        _processNext()
    }

    // --- Step for an entity ---
    function _processNext() {
        var total = instanciator.entityCount()
        if (_currentEntity >= total) {
            _running = false
            statusLabel.text = "Done — " + total + " instance(s) created."
            pipelineBatcherBackend.next()
            return
        }

        statusLabel.text = "Creating instance " + (_currentEntity + 1) + " / " + total + "..."

        // Create nodes
        var nodes = instanciator.createInstanceForEntity(_currentEntity, _yOffset)

        if (!nodes || nodes.length === 0) {
            statusLabel.text = "Error on entity " + _currentEntity
            _running = false
            return
        }

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

        // 3. Add backdrop sized to this instance
        var bboxX = minX - padding
        var bboxY = minY - 2 * padding
        var bboxW = Math.round(maxX - minX + 2 * padding)
        var bboxH = Math.round(maxY - minY + 3 * padding)

        // Create Backdrop wrapping the created pipeline instance
        var backdrop = _currentScene.addBackdropNode(Qt.point(bboxX, bboxY), bboxW, bboxH)
        // Set backdrop label
        instanciator.setBackdropLabel(backdrop, instanciator.entityLabel(_currentEntity))

        // Update the Y padding for next instance and iterate
        _yOffset = Math.round(maxY + padding * 4)
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
        anchors.centerIn: parent
        spacing: 16

        BusyIndicator {
            Layout.alignment: Qt.AlignHCenter
            running: _running
        }

        Label {
            id: statusLabel
            Layout.alignment: Qt.AlignHCenter
            font.pixelSize: 14
        }

        ProgressBar {
            Layout.preferredWidth: 300
            Layout.alignment: Qt.AlignHCenter
            visible: instanciator !== null
            value: instanciator ? _currentEntity / instanciator.entityCount() : 0
        }
    }
}